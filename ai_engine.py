import re
import json
from groq import Groq

class AIEngine:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
            except Exception as e:
                print(f"⚠️  Groq init error: {e}")
    
    def nl_to_dapine(self, query, schema, table_name):
        """Convert natural language to Dapine command using Groq AI."""
        
        # Try Groq first
        if self.client:
            try:
                return self._groq_convert(query, schema, table_name)
            except Exception as e:
                print(f"⚠️  Groq failed, using pattern matching: {e}")
        
        # Fallback to pattern matching
        return self._pattern_match(query, schema, table_name)
    
    def _groq_convert(self, query, schema, table_name):
        """Use Groq to convert NL to Dapine."""
        prompt = f"""You are a Dapine code generator. Convert natural language to Dapine pipeline code.

Available table: {table_name}
Schema: {', '.join(schema)}

Dapine commands:
- filter {table_name} where CONDITION as name
- sort {table_name} by COLUMN asc/desc as name
- limit {table_name} N as name
- mutate {table_name} add NEW_COL = EXPRESSION as name
- group {table_name} by COLUMN [count(COL) as total, sum(COL) as sum_val, avg(COL) as avg_val, min(COL) as min_val, max(COL) as max_val] as name
- select COL1, COL2 from {table_name} as name
- chart {table_name} VALUE_COL by LABEL_COL as bar/pie/line into "chart.html"
- stats {table_name}
- print {table_name}

Return ONLY valid Dapine code. No explanations. One command per line.

Examples:
Q: "show me houses over 400k"
A: filter {table_name} where price > 400000 as filtered
print filtered

Q: "what's the average price per bedroom"
A: group {table_name} by bedrooms [avg(price) as avg_price, count(price) as count] as grouped
print grouped

Q: "top 5 most expensive"
A: sort {table_name} by price desc as sorted
limit sorted 5 as top
print top

Q: "bar chart of prices by bedrooms"
A: chart {table_name} price by bedrooms as bar into "chart.html"

Now convert: {query}"""
        
        response = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        dapine_code = response.choices[0].message.content.strip()
        return dapine_code
    
    def _pattern_match(self, query, schema, table_name):
        """Smart pattern matching fallback."""
        query_lower = query.lower()
        
        # FILTER: price
        if any(w in query_lower for w in ["expensive", "over", "above", "more than"]):
            match = re.search(r'(\d+)\s*k', query_lower)
            if match:
                price = int(match.group(1)) * 1000
                return f"filter {table_name} where price > {price} as filtered\nprint filtered"
            match = re.search(r'(\d+)0{3,}', query_lower.replace(',',''))
            if match:
                return f"filter {table_name} where price > {int(match.group(1))} as filtered\nprint filtered"
        
        if any(w in query_lower for w in ["cheap", "under", "below", "less than"]):
            match = re.search(r'(\d+)\s*k', query_lower)
            if match:
                price = int(match.group(1)) * 1000
                return f"filter {table_name} where price < {price} as filtered\nprint filtered"
        
        # FILTER: bedrooms
        match = re.search(r'(\d+)\s*(bed|br|bedroom)', query_lower)
        if match:
            beds = int(match.group(1))
            return f"filter {table_name} where bedrooms >= {beds} as filtered\nprint filtered"
        
        # FILTER: bathrooms
        match = re.search(r'(\d+)\s*(bath|ba|bathroom)', query_lower)
        if match:
            baths = int(match.group(1))
            return f"filter {table_name} where bathrooms >= {baths} as filtered\nprint filtered"
        
        # GROUP BY
        if any(w in query_lower for w in ["average", "avg", "mean"]):
            for col in schema:
                if col in query_lower and col != "price":
                    return f"group {table_name} by {col} [avg(price) as avg_price, count(price) as count] as grouped\nprint grouped"
            return f"group {table_name} by bedrooms [avg(price) as avg_price, count(price) as count] as grouped\nprint grouped"
        
        if any(w in query_lower for w in ["per", "by"]):
            for col in schema:
                if col in query_lower and col != "price":
                    return f"group {table_name} by {col} [count(price) as count, avg(price) as avg_price] as grouped\nprint grouped"
        
        # SORT + LIMIT
        if "top" in query_lower or "highest" in query_lower or "most" in query_lower:
            num = re.search(r'top\s*(\d+)', query_lower)
            limit = int(num.group(1)) if num else 5
            return f"sort {table_name} by price desc as sorted\nlimit sorted {limit} as top\nprint top"
        
        # CHART
        if any(w in query_lower for w in ["chart", "graph", "plot", "visualize"]):
            chart_type = "bar"
            if "pie" in query_lower: chart_type = "pie"
            if "line" in query_lower: chart_type = "line"
            if "scatter" in query_lower: chart_type = "scatter"
            return f"chart {table_name} price by bedrooms as {chart_type} into \"chart.html\""
        
        # STATS
        if any(w in query_lower for w in ["stats", "statistics", "summary", "describe"]):
            return f"stats {table_name}"
        
        # Default: show the data
        return f"print {table_name}"