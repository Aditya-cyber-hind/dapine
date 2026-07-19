import csv
import json
import urllib.request
import random
import statistics
import math
from datetime import date, datetime, timedelta
from errors import RuntimeError, ColumnNotFoundError, DataFrameNotFoundError
from ast_nodes import *

class DataFrame:
    def __init__(self, rows, schema, lineage=""):
        self.rows = rows
        self.schema = schema
        self.lineage = lineage

    def __repr__(self):
        return f"DataFrame(rows={len(self.rows)}, schema={self.schema})"

class Runtime:
    def __init__(self):
        self.dataframes = {}
        self.lineage_log = []
        self.variables = {}
        self.functions = {}
        self.pipelines = {}
        self.ml_engine = None
        self.duck = None
        self.use_duckdb = True

    def log_lineage(self, target, source, transformation):
        entry = f"[{target}] <- {transformation} <- [{source}]"
        self.lineage_log.append(entry)

    def get_df(self, name, line=None):
        if name not in self.dataframes:
            available = list(self.dataframes.keys())
            raise DataFrameNotFoundError(name, available, line)
        return self.dataframes[name]

    def check_column(self, df, column, line=None):
        if column not in df.schema:
            raise ColumnNotFoundError(column, df.schema, line)

    def _get_duck(self):
        if self.duck is None:
            from duck_engine import DuckEngine
            self.duck = DuckEngine()
        return self.duck

    def _df_to_duck(self, name):
        df = self.dataframes.get(name)
        if df:
            duck = self._get_duck()
            duck.register_df(name, df.rows, df.schema)

    def _duck_to_df(self, table_name, lineage=""):
        duck = self._get_duck()
        rows, schema = duck._table_to_rows(table_name)
        return DataFrame(rows, schema, lineage)

    # ============ STEP EXECUTION ============

    def execute_step(self, step):
        if isinstance(step, ReadStep): return self.execute_read(step)
        elif isinstance(step, HttpReadStep): return self.execute_http_read(step)
        elif isinstance(step, FilterStep): return self.execute_filter(step)
        elif isinstance(step, SelectStep): return self.execute_select(step)
        elif isinstance(step, JoinStep): return self.execute_join(step)
        elif isinstance(step, GroupStep): return self.execute_group(step)
        elif isinstance(step, WriteStep): self.execute_write(step)
        elif isinstance(step, SortStep): return self.execute_sort(step)
        elif isinstance(step, DistinctStep): return self.execute_distinct(step)
        elif isinstance(step, LimitStep): return self.execute_limit(step)
        elif isinstance(step, MutateStep): return self.execute_mutate(step)
        elif isinstance(step, UnionStep): return self.execute_union(step)
        elif isinstance(step, RenameStep): return self.execute_rename(step)
        elif isinstance(step, PrintStep): return self.execute_print(step)
        elif isinstance(step, LetStep): return self.execute_let(step)
        elif isinstance(step, CastStep): return self.execute_cast(step)
        elif isinstance(step, SampleStep): return self.execute_sample(step)
        elif isinstance(step, StatsStep): return self.execute_stats(step)
        elif isinstance(step, IfStep): return self.execute_if(step)
        elif isinstance(step, ChartStep): return self.execute_chart(step)
        elif isinstance(step, TrainStep): return self.execute_train(step)
        elif isinstance(step, PredictStep): return self.execute_predict(step)
        elif isinstance(step, DBReadStep): return self.execute_db_read(step)
        elif isinstance(step, DBWriteStep): self.execute_db_write(step)
        elif isinstance(step, ExcelReadStep): return self.execute_excel_read(step)
        elif isinstance(step, ExcelWriteStep): self.execute_excel_write(step)
        elif isinstance(step, ReportStep): return self.execute_report(step)
        return None

    def execute_read(self, step):
        if self.use_duckdb and step.format_type in ("csv", "json"):
            duck = self._get_duck()
            table_name = step.alias or f"_tbl_{len(self.dataframes)}"
            if step.format_type == "csv":
                rows, schema = duck.load_csv(step.source, table_name)
            else:
                rows, schema = duck.load_json(step.source, table_name)
            name = step.alias or f"_df_{len(self.dataframes)}"
            df = DataFrame(rows, schema, f"read {step.format_type} from {step.source}")
            self.dataframes[name] = df
            self.log_lineage(name, step.source, f"READ {step.format_type.upper()}")
            return df
        
        if step.format_type == "csv":
            try:
                with open(step.source, "r") as f:
                    reader = csv.DictReader(f)
                    rows = []
                    for row in reader:
                        typed_row = {}
                        for key, value in row.items():
                            typed_row[key] = self._infer_type(value)
                        rows.append(typed_row)
                    schema = list(rows[0].keys()) if rows else []
                    df = DataFrame(rows, schema, f"read csv from {step.source}")
                    name = step.alias or f"_df_{len(self.dataframes)}"
                    self.dataframes[name] = df
                    self.log_lineage(name, step.source, "READ CSV")
                    return df
            except FileNotFoundError:
                raise RuntimeError(f"File not found: '{step.source}'", step.line)
        elif step.format_type == "json":
            try:
                with open(step.source, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict): data = [data]
                    if isinstance(data, list):
                        rows = data
                        schema = list(rows[0].keys()) if rows else []
                        df = DataFrame(rows, schema, f"read json from {step.source}")
                        name = step.alias or f"_df_{len(self.dataframes)}"
                        self.dataframes[name] = df
                        self.log_lineage(name, step.source, "READ JSON")
                        return df
            except FileNotFoundError:
                raise RuntimeError(f"File not found: '{step.source}'", step.line)
        raise RuntimeError(f"Unsupported format: {step.format_type}", step.line)

    def execute_http_read(self, step):
        try:
            with urllib.request.urlopen(step.url) as response:
                data = response.read().decode("utf-8")
                if step.format_type == "json":
                    rows = json.loads(data)
                    if isinstance(rows, dict): rows = [rows]
                    schema = list(rows[0].keys()) if rows else []
                    df = DataFrame(rows, schema, f"http read from {step.url}")
                    name = step.alias or f"_df_{len(self.dataframes)}"
                    self.dataframes[name] = df
                    self.log_lineage(name, step.url, "HTTP READ")
                    return df
        except Exception as e:
            raise RuntimeError(f"HTTP read failed: {e}", step.line)

    def execute_let(self, step):
        value = self._eval_atomic(step.value, {})
        self.variables[step.var_name] = value
        return value

    def execute_filter(self, step):
        if self.use_duckdb and step.input_ref in self.dataframes:
            self._df_to_duck(step.input_ref)
            duck = self._get_duck()
            alias = step.alias or f"_tbl_{len(self.dataframes)}"
            cond_str = self._condition_to_sql(step.condition)
            duck.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS SELECT * FROM {step.input_ref} WHERE {cond_str}")
            df = self._duck_to_df(alias, f"filter from {step.input_ref}")
            name = step.alias or f"_df_{len(self.dataframes)}"
            self.dataframes[name] = df
            self.log_lineage(name, step.input_ref, "FILTER")
            return df
        
        df = self.get_df(step.input_ref, step.line)
        filtered = []
        for row in df.rows:
            if self.eval_condition(step.condition, row):
                filtered.append(row)
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(filtered, df.schema, f"filter from {step.input_ref}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, "FILTER")
        return new_df

    def _condition_to_sql(self, expr):
        if isinstance(expr, BinaryOp):
            left = self._cond_to_sql_part(expr.left)
            right = self._cond_to_sql_part(expr.right)
            op_map = {"==": "=", "!=": "<>", "and": "AND", "or": "OR",
                      ">": ">", "<": "<", ">=": ">=", "<=": "<="}
            op = op_map.get(expr.op, expr.op.upper())
            return f"({left} {op} {right})"
        return "1=1"

    def _cond_to_sql_part(self, expr):
        if isinstance(expr, Identifier):
            return f'"{expr.name}"'
        elif isinstance(expr, ColumnRef):
            return f'"{expr.column}"'
        elif isinstance(expr, StringLiteral):
            return f"'{expr.value}'"
        elif isinstance(expr, NumberLiteral):
            return str(expr.value)
        return "NULL"

    def execute_select(self, step):
        df = self.get_df(step.input_ref, step.line)
        for col in step.columns:
            self.check_column(df, col, step.line)
        selected = [{col: row.get(col, None) for col in step.columns} for row in df.rows]
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(selected, step.columns, f"select from {step.input_ref}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"SELECT {step.columns}")
        return new_df

    def execute_join(self, step):
        left = self.get_df(step.left_ref, step.line)
        right = self.get_df(step.right_ref, step.line)
        self.check_column(left, step.on_column, step.line)
        self.check_column(right, step.on_column, step.line)
        joined = []
        for lrow in left.rows:
            matched = False
            for rrow in right.rows:
                if lrow.get(step.on_column) == rrow.get(step.on_column):
                    joined.append({**lrow, **rrow})
                    matched = True
            if step.join_type == "left" and not matched:
                joined.append({**lrow, **{k: None for k in right.schema}})
        name = step.alias or f"_df_{len(self.dataframes)}"
        schema = left.schema + [c for c in right.schema if c not in left.schema]
        new_df = DataFrame(joined, schema, f"{step.join_type} join")
        self.dataframes[name] = new_df
        self.log_lineage(name, f"{step.left_ref},{step.right_ref}", f"JOIN on {step.on_column}")
        return new_df

    def execute_group(self, step):
        df = self.get_df(step.input_ref, step.line)
        self.check_column(df, step.key_column, step.line)
        groups = {}
        for row in df.rows:
            key = row.get(step.key_column)
            if key not in groups: groups[key] = []
            groups[key].append(row)
        result = []
        for key, rows in groups.items():
            out_row = {step.key_column: key}
            for agg in step.aggregations:
                if agg.func == "count":
                    out_row[agg.output_name] = len(rows)
                else:
                    self.check_column(df, agg.column, step.line)
                    values = []
                    for r in rows:
                        val = r.get(agg.column)
                        if val is not None:
                            try: values.append(float(val))
                            except: pass
                    if agg.func == "sum": out_row[agg.output_name] = sum(values)
                    elif agg.func == "avg": out_row[agg.output_name] = sum(values)/len(values) if values else 0
                    elif agg.func == "min": out_row[agg.output_name] = min(values) if values else None
                    elif agg.func == "max": out_row[agg.output_name] = max(values) if values else None
            result.append(out_row)
        name = step.alias or f"_df_{len(self.dataframes)}"
        schema = [step.key_column] + [a.output_name for a in step.aggregations]
        new_df = DataFrame(result, schema, f"group by {step.key_column}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"GROUP BY {step.key_column}")
        return new_df

    def execute_write(self, step):
        df = self.get_df(step.input_ref, step.line)
        if step.format_type == "csv":
            with open(step.target, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=df.schema)
                writer.writeheader()
                writer.writerows(df.rows)
        elif step.format_type == "json":
            with open(step.target, "w") as f:
                json.dump(df.rows, f, indent=2, default=str)
        else:
            raise RuntimeError(f"Unsupported write format: {step.format_type}", step.line)
        self.log_lineage(step.target, step.input_ref, f"WRITE {step.format_type}")
        print(f"✓ Written {len(df.rows)} rows to {step.target}")

    def execute_sort(self, step):
        df = self.get_df(step.input_ref, step.line)
        self.check_column(df, step.column, step.line)
        reverse = step.direction == "desc"
        sorted_rows = sorted(df.rows, key=lambda r: (r.get(step.column) is None, r.get(step.column, "")), reverse=reverse)
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(sorted_rows, df.schema, f"sort by {step.column}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"SORT BY {step.column} {step.direction}")
        return new_df

    def execute_distinct(self, step):
        df = self.get_df(step.input_ref, step.line)
        seen = set()
        unique = []
        for row in df.rows:
            key = tuple(sorted(str(v) for v in row.items()))
            if key not in seen:
                seen.add(key)
                unique.append(row)
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(unique, df.schema, "distinct")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, "DISTINCT")
        return new_df

    def execute_limit(self, step):
        df = self.get_df(step.input_ref, step.line)
        limited = df.rows[:step.count]
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(limited, df.schema, f"limit {step.count}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"LIMIT {step.count}")
        return new_df

    def execute_mutate(self, step):
        df = self.get_df(step.input_ref, step.line)
        mutated = []
        for i, row in enumerate(df.rows):
            new_row = dict(row)
            try:
                new_row[step.new_column] = self.eval_arithmetic(step.expression, row)
            except Exception as e:
                raise RuntimeError(f"Mutate failed on row {i}: {e}", step.line)
            mutated.append(new_row)
        schema = df.schema + [step.new_column]
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(mutated, schema, f"mutate add {step.new_column}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"MUTATE add {step.new_column}")
        return new_df

    def execute_union(self, step):
        left = self.get_df(step.left_ref, step.line)
        right = self.get_df(step.right_ref, step.line)
        all_schema = list(dict.fromkeys(left.schema + right.schema))
        merged = left.rows + right.rows
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(merged, all_schema, "union")
        self.dataframes[name] = new_df
        self.log_lineage(name, f"{step.left_ref},{step.right_ref}", "UNION")
        return new_df

    def execute_rename(self, step):
        df = self.get_df(step.input_ref, step.line)
        for old in step.renames:
            self.check_column(df, old, step.line)
        renamed = []
        for row in df.rows:
            new_row = {}
            for k, v in row.items():
                new_row[step.renames.get(k, k)] = v
            renamed.append(new_row)
        schema = [step.renames.get(c, c) for c in df.schema]
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(renamed, schema, "rename")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"RENAME {step.renames}")
        return new_df

    def execute_print(self, step):
        df = self.get_df(step.input_ref, step.line)
        print(f"\n  📊 {step.input_ref}: {len(df.rows)} rows × {len(df.schema)} cols")
        print(f"  Columns: {', '.join(df.schema)}")
        print(f"  {'─'*50}")
        for row in df.rows[:20]:
            print(f"  {row}")
        if len(df.rows) > 20:
            print(f"  ... and {len(df.rows)-20} more rows")
        print(f"  {'─'*50}\n")
        return df

    def execute_cast(self, step):
        df = self.get_df(step.input_ref, step.line)
        self.check_column(df, step.column, step.line)
        for row in df.rows:
            val = row.get(step.column)
            try:
                if step.new_type == "int": row[step.column] = int(float(val)) if val is not None else None
                elif step.new_type == "float": row[step.column] = float(val) if val is not None else None
                elif step.new_type == "string": row[step.column] = str(val) if val is not None else ""
                elif step.new_type == "bool": row[step.column] = bool(val)
                elif step.new_type == "date":
                    if isinstance(val, str): row[step.column] = date.fromisoformat(val)
            except Exception as e:
                raise RuntimeError(f"Cast failed: {e}", step.line)
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(list(df.rows), df.schema, f"cast {step.column} to {step.new_type}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"CAST {step.column} → {step.new_type}")
        return new_df

    def execute_sample(self, step):
        df = self.get_df(step.input_ref, step.line)
        k = max(1, int(len(df.rows) * step.percent / 100))
        sampled = random.sample(df.rows, min(k, len(df.rows)))
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(sampled, df.schema, f"sample {step.percent}%")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"SAMPLE {step.percent}%")
        return new_df

    def execute_stats(self, step):
        df = self.get_df(step.input_ref, step.line)
        print(f"\n  📈 STATS: {step.input_ref} ({len(df.rows)} rows)")
        print(f"  {'─'*50}")
        for col in df.schema:
            values = []
            for r in df.rows:
                v = r.get(col)
                if isinstance(v, (int, float)): values.append(v)
            if values:
                if len(values) > 1:
                    print(f"  {col}: min={min(values)}, max={max(values)}, mean={statistics.mean(values):.2f}, median={statistics.median(values):.2f}, stdev={statistics.stdev(values):.2f}")
                else:
                    print(f"  {col}: value={values[0]}")
            else:
                print(f"  {col}: (non-numeric)")
        print(f"  {'─'*50}\n")
        return df

    def execute_for(self, step):
        df = self.get_df(step.input_ref, step.line)
        for row in df.rows:
            self.variables[step.row_var] = row
            for s in step.body:
                self.execute_step(s)
        return df

    def execute_case(self, step):
        df = self.get_df(step.input_ref, step.line)
        self.check_column(df, step.column, step.line)
        for row in df.rows:
            val = row.get(step.column)
            matched = False
            for case in step.cases:
                if val == self._eval_atomic(case.value, row):
                    matched = True
                    for s in case.body: self.execute_step(s)
                    break
            if not matched and step.default_alias:
                for s in step.default_alias: self.execute_step(s)
        return df

    def execute_if(self, step):
        if self.eval_condition(step.condition, {}):
            for s in step.if_body: self.execute_step(s)
        elif step.else_body:
            for s in step.else_body: self.execute_step(s)
        return None

    def execute_chart(self, step):
        from charts import ChartEngine
        ChartEngine(self).generate_chart(step.input_ref, step.chart_type, step.label_col, step.value_col, step.title, step.target)
        return None

    def execute_train(self, step):
        from ml_engine import MLEngine
        if self.ml_engine is None: self.ml_engine = MLEngine()
        df = self.get_df(step.input_ref, step.line)
        result = self.ml_engine.train(df, step.target_col, step.model_type, step.model_name)
        print(f"\n  🤖 Model Trained: {step.model_name}")
        print(f"  {'─'*50}")
        for k, v in result.items():
            if k != "metrics": print(f"  {k}: {v}")
        print(f"  Metrics: {json.dumps(result.get('metrics', {}), indent=2)}")
        print(f"  {'─'*50}\n")
        return None

    def execute_predict(self, step):
        from ml_engine import MLEngine
        if self.ml_engine is None: self.ml_engine = MLEngine()
        df = self.get_df(step.input_ref, step.line)
        new_rows, new_schema = self.ml_engine.predict(df, step.model_name, step.output_col)
        if new_rows is None:
            print(f"Error: {new_schema.get('error')}")
            return None
        name = step.alias or f"_df_{len(self.dataframes)}"
        new_df = DataFrame(new_rows, new_schema, f"predict using {step.model_name}")
        self.dataframes[name] = new_df
        self.log_lineage(name, step.input_ref, f"PREDICT using {step.model_name}")
        return new_df

    def execute_db_read(self, step):
        from connectors import Connectors
        conn = Connectors()
        rows, columns = conn.read_database(step.connection_string, step.query, step.alias)
        name = step.alias or f"_df_{len(self.dataframes)}"
        df = DataFrame(rows, columns, f"db read")
        self.dataframes[name] = df
        self.log_lineage(name, "database", "DB READ")
        return df

    def execute_db_write(self, step):
        from connectors import Connectors
        df = self.get_df(step.input_ref, step.line)
        conn = Connectors()
        conn.write_database(df.rows, df.schema, step.connection_string, step.table_name)
        print(f"✓ Written {len(df.rows)} rows to database table '{step.table_name}'")
        self.log_lineage(step.table_name, step.input_ref, "DB WRITE")

    def execute_excel_read(self, step):
        from connectors import Connectors
        conn = Connectors()
        rows, columns = conn.read_excel(step.source, step.sheet_name)
        name = step.alias or f"_df_{len(self.dataframes)}"
        df = DataFrame(rows, columns, f"excel read from {step.source}")
        self.dataframes[name] = df
        self.log_lineage(name, step.source, "EXCEL READ")
        return df

    def execute_excel_write(self, step):
        from connectors import Connectors
        df = self.get_df(step.input_ref, step.line)
        conn = Connectors()
        conn.write_excel(df.rows, df.schema, step.target, step.sheet_name)
        print(f"✓ Written {len(df.rows)} rows to {step.target}")
        self.log_lineage(step.target, step.input_ref, "EXCEL WRITE")

    def execute_report(self, step):
        from reports import ReportEngine
        ReportEngine(self).generate_report(step.input_ref, step.title, step.target)
        return None

    # ============ TYPE INFERENCE ============

    def _infer_type(self, value):
        value = value.strip()
        if value == "" or value.lower() in ("null", "none"): return None
        if value.lower() == "true": return True
        if value.lower() == "false": return False
        try: return int(value)
        except: pass
        try: return float(value)
        except: pass
        try: return date.fromisoformat(value)
        except: pass
        return value

    # ============ EXPRESSION EVALUATION ============

    def _eval_atomic(self, expr, row):
        if isinstance(expr, BinaryOp): return self.eval_condition(expr, row)
        elif isinstance(expr, ArithOp): return self.eval_arithmetic(expr, row)
        elif isinstance(expr, FuncCall): return self._eval_func_call(expr, row)
        elif isinstance(expr, ColumnRef): return row.get(expr.column)
        elif isinstance(expr, Identifier):
            if expr.name in self.variables: return self.variables[expr.name]
            return row.get(expr.name)
        elif isinstance(expr, StringLiteral): return expr.value
        elif isinstance(expr, NumberLiteral): return expr.value
        elif isinstance(expr, BooleanLiteral): return expr.value
        elif isinstance(expr, DateLiteral): return expr.value
        elif isinstance(expr, NullLiteral): return None
        return None

    def _eval_func_call(self, expr, row):
        if expr.name in self.functions:
            func = self.functions[expr.name]
            saved_vars = dict(self.variables)
            for i, param in enumerate(func.params):
                if i < len(expr.args):
                    self.variables[param] = self._eval_atomic(expr.args[i], row)
            result = self._eval_atomic(func.body_expr, row)
            self.variables = saved_vars
            return result

        args = [self._eval_atomic(a, row) for a in expr.args]
        
        if expr.name == "upper": return str(args[0]).upper() if args[0] is not None else ""
        elif expr.name == "lower": return str(args[0]).lower() if args[0] is not None else ""
        elif expr.name == "length": return len(str(args[0])) if args[0] is not None else 0
        elif expr.name == "trim": return str(args[0]).strip() if args[0] is not None else ""
        elif expr.name == "concat": return "".join(str(a) for a in args)
        elif expr.name == "abs": return abs(args[0]) if args[0] is not None else None
        elif expr.name == "round": return round(args[0], args[1] if len(args)>1 else 0) if args[0] is not None else None
        elif expr.name == "ceil": return math.ceil(args[0]) if args[0] is not None else None
        elif expr.name == "floor": return math.floor(args[0]) if args[0] is not None else None
        elif expr.name == "sqrt": return math.sqrt(args[0]) if args[0] is not None and args[0] >= 0 else None
        elif expr.name == "pow": return math.pow(args[0], args[1]) if len(args)>1 else None
        elif expr.name == "year": return args[0].year if isinstance(args[0], date) else None
        elif expr.name == "month": return args[0].month if isinstance(args[0], date) else None
        elif expr.name == "day": return args[0].day if isinstance(args[0], date) else None
        elif expr.name == "today": return date.today()
        elif expr.name == "now": return datetime.now()
        elif expr.name == "date_add":
            if len(args)>=2 and isinstance(args[0], date): return args[0] + timedelta(days=args[1])
        elif expr.name == "date_diff":
            if len(args)>=2 and isinstance(args[0], date) and isinstance(args[1], date): return (args[0]-args[1]).days
        elif expr.name == "date_format":
            if len(args)>=2 and isinstance(args[0], date): return args[0].strftime(str(args[1]))
        elif expr.name == "day_name": return args[0].strftime("%A") if isinstance(args[0], date) else None
        elif expr.name == "month_name": return args[0].strftime("%B") if isinstance(args[0], date) else None
        return None

    def eval_condition(self, expr, row):
        if isinstance(expr, BinaryOp):
            left = self._eval_atomic(expr.left, row)
            right = self._eval_atomic(expr.right, row)
            if expr.op == "contains": return str(left).find(str(right)) >= 0 if left and right else False
            if expr.op == "starts_with": return str(left).startswith(str(right)) if left and right else False
            if expr.op == "ends_with": return str(left).endswith(str(right)) if left and right else False
            if expr.op == "matches":
                import re
                try: return bool(re.search(str(right), str(left))) if left and right else False
                except: return False
            if expr.op == "is": return left is None
            if expr.op == "is_not": return left is not None
            if left is None and right is None:
                return expr.op == "=="
            if left is None or right is None:
                return expr.op == "!="
            left, right = self._coerce_types(left, right)
            if expr.op == "==": return left == right
            if expr.op == "!=": return left != right
            if expr.op == ">": return left > right
            if expr.op == "<": return left < right
            if expr.op == ">=": return left >= right
            if expr.op == "<=": return left <= right
            if expr.op == "and": return left and right
            if expr.op == "or": return left or right
        else:
            return self._eval_atomic(expr, row)

    def eval_arithmetic(self, expr, row):
        if isinstance(expr, ArithOp):
            left = self._eval_atomic(expr.left, row) or 0
            right = self._eval_atomic(expr.right, row) or 0
            if expr.op == "+":
                if isinstance(left, str) or isinstance(right, str): return str(left) + str(right)
                return left + right
            if expr.op == "-": return left - right
            if expr.op == "*": return left * right
            if expr.op == "/": return left / right if right != 0 else None
        else:
            return self._eval_atomic(expr, row)

    def _coerce_types(self, left, right):
        if isinstance(left, date) and isinstance(right, str):
            try: right = date.fromisoformat(right)
            except: pass
        elif isinstance(right, date) and isinstance(left, str):
            try: left = date.fromisoformat(left)
            except: pass
        if isinstance(left, str) and isinstance(right, (int, float)):
            try: left = float(left)
            except: pass
        elif isinstance(right, str) and isinstance(left, (int, float)):
            try: right = float(right)
            except: pass
        return left, right