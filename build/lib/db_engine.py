import duckdb
import csv
import json
import os

class DBEngine:
    def __init__(self):
        self.conn = duckdb.connect(database=':memory:')
        self.tables = {}
    
    def load_csv(self, name, filepath):
        """Load a CSV into DuckDB."""
        self.conn.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_csv_auto('{filepath}')")
        result = self.conn.execute(f"SELECT * FROM {name}").fetchall()
        columns = [desc[0] for desc in self.conn.description]
        rows = [dict(zip(columns, row)) for row in result]
        self.tables[name] = {"rows": rows, "columns": columns}
        return rows, columns
    
    def load_json(self, name, filepath):
        """Load a JSON into DuckDB."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        columns = list(data[0].keys()) if data else []
        self.conn.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM read_json_auto('{filepath}')")
        result = self.conn.execute(f"SELECT * FROM {name}").fetchall()
        rows = [dict(zip(columns, row)) for row in result]
        self.tables[name] = {"rows": rows, "columns": columns}
        return rows, columns
    
    def register_dataframe(self, name, rows, columns):
        """Register in-memory data as a DuckDB table."""
        if not rows:
            return
        self.conn.execute(f"DROP TABLE IF EXISTS {name}")
        col_defs = ", ".join([f'"{c}" VARCHAR' for c in columns])
        self.conn.execute(f"CREATE TABLE {name} ({col_defs})")
        
        for row in rows:
            values = []
            for c in columns:
                val = row.get(c, None)
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    escaped = val.replace("'", "''")
                    values.append(f"'{escaped}'")
                elif isinstance(val, bool):
                    values.append(str(val).upper())
                else:
                    values.append(str(val))
            vals_str = ", ".join(values)
            self.conn.execute(f"INSERT INTO {name} VALUES ({vals_str})")
        
        self.tables[name] = {"rows": rows, "columns": columns}
    
    def execute_sql(self, sql):
        """Run raw SQL and return results."""
        result = self.conn.execute(sql).fetchall()
        columns = [desc[0] for desc in self.conn.description]
        rows = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in result]
        return rows, columns
    
    def close(self):
        self.conn.close()