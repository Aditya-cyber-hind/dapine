import duckdb
import json
import os
from datetime import date, datetime

class DuckEngine:
    def __init__(self):
        self.conn = duckdb.connect(database=':memory:')
        self.conn.execute("INSTALL json; LOAD json;")
    
    def load_csv(self, filepath, table_name):
        """Load CSV into DuckDB."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{filepath}')")
        return self._table_to_rows(table_name)
    
    def load_json(self, filepath, table_name):
        """Load JSON into DuckDB."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto('{filepath}')")
        return self._table_to_rows(table_name)
    
    def register_df(self, name, rows, columns):
        """Register in-memory DataFrame as DuckDB table."""
        if not rows:
            return
        self.conn.execute(f"DROP TABLE IF EXISTS {name}")
        
        # Create table with inferred types
        col_defs = []
        for c in columns:
            sample_vals = [r.get(c) for r in rows[:10] if r.get(c) is not None]
            if all(isinstance(v, bool) for v in sample_vals):
                col_defs.append(f'"{c}" BOOLEAN')
            elif all(isinstance(v, int) for v in sample_vals):
                col_defs.append(f'"{c}" BIGINT')
            elif all(isinstance(v, (int, float)) for v in sample_vals):
                col_defs.append(f'"{c}" DOUBLE')
            else:
                col_defs.append(f'"{c}" VARCHAR')
        
        col_str = ", ".join(col_defs)
        self.conn.execute(f"CREATE TABLE {name} ({col_str})")
        
        # Insert rows in batches
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            values_list = []
            for row in batch:
                vals = []
                for c in columns:
                    v = row.get(c)
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, bool):
                        vals.append("TRUE" if v else "FALSE")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        escaped = str(v).replace("'", "''")
                        vals.append(f"'{escaped}'")
                values_list.append(f"({', '.join(vals)})")
            
            if values_list:
                vals_str = ", ".join(values_list)
                self.conn.execute(f"INSERT INTO {name} VALUES {vals_str}")
    
    def execute_sql(self, sql):
        """Execute SQL and return results."""
        result = self.conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = []
        for row in result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                if isinstance(val, (date, datetime)):
                    val = str(val)
                row_dict[col] = val
            rows.append(row_dict)
        return rows, columns
    
    def filter_table(self, table_name, condition, alias):
        """Filter using DuckDB SQL."""
        sql = f"SELECT * FROM {table_name} WHERE {self._dap_to_sql(condition)}"
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def sort_table(self, table_name, column, direction, alias):
        """Sort using DuckDB."""
        sql = f"SELECT * FROM {table_name} ORDER BY \"{column}\" {direction.upper()}"
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def limit_table(self, table_name, count, alias):
        """Limit using DuckDB."""
        sql = f"SELECT * FROM {table_name} LIMIT {count}"
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def group_table(self, table_name, key_col, aggs, alias):
        """Group by using DuckDB."""
        agg_parts = []
        for agg in aggs:
            if agg["func"] == "count":
                agg_parts.append(f'COUNT("{agg["column"]}") AS "{agg["output"]}"')
            elif agg["func"] == "sum":
                agg_parts.append(f'SUM(CAST("{agg["column"]}" AS DOUBLE)) AS "{agg["output"]}"')
            elif agg["func"] == "avg":
                agg_parts.append(f'AVG(CAST("{agg["column"]}" AS DOUBLE)) AS "{agg["output"]}"')
            elif agg["func"] == "min":
                agg_parts.append(f'MIN(CAST("{agg["column"]}" AS DOUBLE)) AS "{agg["output"]}"')
            elif agg["func"] == "max":
                agg_parts.append(f'MAX(CAST("{agg["column"]}" AS DOUBLE)) AS "{agg["output"]}"')
        
        agg_str = ", ".join(agg_parts)
        sql = f'SELECT "{key_col}", {agg_str} FROM {table_name} GROUP BY "{key_col}"'
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def join_tables(self, left, right, on_col, join_type, alias):
        """Join using DuckDB."""
        join_map = {"inner": "INNER", "left": "LEFT", "right": "RIGHT"}
        sql = f'SELECT * FROM {left} {join_map.get(join_type, "INNER")} JOIN {right} ON {left}."{on_col}" = {right}."{on_col}"'
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def mutate_table(self, table_name, new_col, expression, alias):
        """Add calculated column using DuckDB."""
        sql = f'SELECT *, ({self._dap_to_sql(expression)}) AS "{new_col}" FROM {table_name}'
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def select_columns(self, table_name, columns, alias):
        """Select columns using DuckDB."""
        col_str = ", ".join([f'"{c}"' for c in columns])
        sql = f"SELECT {col_str} FROM {table_name}"
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def distinct_table(self, table_name, alias):
        """Distinct using DuckDB."""
        sql = f"SELECT DISTINCT * FROM {table_name}"
        self.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS {sql}")
        return self._table_to_rows(alias)
    
    def get_stats(self, table_name):
        """Get statistics using DuckDB."""
        columns = self._get_columns(table_name)
        stats = {}
        for col in columns:
            try:
                result = self.conn.execute(f'''
                    SELECT 
                        MIN(CAST("{col}" AS DOUBLE)) as min_val,
                        MAX(CAST("{col}" AS DOUBLE)) as max_val,
                        AVG(CAST("{col}" AS DOUBLE)) as mean_val,
                        MEDIAN(CAST("{col}" AS DOUBLE)) as median_val,
                        STDDEV(CAST("{col}" AS DOUBLE)) as std_val
                    FROM {table_name}
                ''').fetchone()
                if result[0] is not None:
                    stats[col] = {
                        "min": result[0], "max": result[1],
                        "mean": result[2], "median": result[3], "stdev": result[4]
                    }
            except:
                pass
        return stats
    
    def _table_to_rows(self, table_name):
        """Convert DuckDB table to list of dicts."""
        columns = self._get_columns(table_name)
        result = self.conn.execute(f"SELECT * FROM {table_name}").fetchall()
        rows = []
        for row in result:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                if isinstance(val, (date, datetime)):
                    val = str(val)
                row_dict[col] = val
            rows.append(row_dict)
        return rows, columns
    
    def _get_columns(self, table_name):
        """Get column names."""
        result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
        return [row[0] for row in result]
    
    def _dap_to_sql(self, expr):
        """Convert Dapine expression to SQL."""
        if expr is None:
            return "NULL"
        if isinstance(expr, str):
            return expr
        # For now, return string representation
        return str(expr)
    
    def table_exists(self, name):
        """Check if table exists."""
        try:
            self.conn.execute(f"SELECT 1 FROM {name} LIMIT 1")
            return True
        except:
            return False
    
    def close(self):
        self.conn.close()