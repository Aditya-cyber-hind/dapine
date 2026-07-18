import csv
import json

BUILTINS = {
    "print_schema": lambda df: print(f"Schema: {df.schema}"),
    "print_rows": lambda df: [print(row) for row in df.rows],
    "count_rows": lambda df: len(df.rows),
    "head": lambda df, n=5: df.rows[:n],
}