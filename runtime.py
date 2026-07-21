import csv
import json
import urllib.request
import random
import statistics
import math
import glob
from datetime import date, datetime, timedelta
from errors import RuntimeError, ColumnNotFoundError, DataFrameNotFoundError
from ast_nodes import *

class DataFrame:
    def __init__(self, rows, schema, lineage=""):
        self.rows = rows
        self.schema = schema
        self.lineage = lineage
        self.inferred_types = {}
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
        self._stdlib_loaded = False
        self.slack_webhook = None

    def log_lineage(self, target, source, transformation):
        self.lineage_log.append(f"[{target}] <- {transformation} <- [{source}]")

    def get_df(self, name, line=None):
        if name not in self.dataframes:
            raise DataFrameNotFoundError(name, list(self.dataframes.keys()), line)
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
            self._get_duck().register_df(name, df.rows, df.schema)

    def _resolve_vars(self, expr):
        if isinstance(expr, Identifier):
            if expr.name in self.variables:
                val = self.variables[expr.name]
                if isinstance(val, str): return StringLiteral(val)
                elif isinstance(val, (int, float)): return NumberLiteral(val)
                elif isinstance(val, bool): return BooleanLiteral(val)
                elif val is None: return NullLiteral()
        elif isinstance(expr, BinaryOp):
            expr.left = self._resolve_vars(expr.left)
            expr.right = self._resolve_vars(expr.right)
        elif isinstance(expr, ArithOp):
            expr.left = self._resolve_vars(expr.left)
            expr.right = self._resolve_vars(expr.right)
        return expr

    # ============ STEP EXECUTION ============

    def execute_step(self, step):
        if not self._stdlib_loaded:
            try:
                from stdlib import StdLib
                StdLib(self).register_all()
            except: pass
            self._stdlib_loaded = True

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
        elif isinstance(step, AlertStep): return self.execute_alert(step)
        return None

    def execute_read(self, step):
        # Multi-file wildcard support
        if '*' in step.source or '?' in step.source:
            files = glob.glob(step.source)
            if not files:
                raise RuntimeError(f"No files match: '{step.source}'", step.line)
            all_rows = []
            schema = None
            for f in sorted(files):
                with open(f, 'r', encoding='utf-8') as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        all_rows.append({k: self._infer_type(v) for k,v in row.items()})
                    if schema is None:
                        schema = reader.fieldnames
            name = step.alias or f"_df_{len(self.dataframes)}"
            df = DataFrame(all_rows, schema or [], f"read {len(files)} files")
            from dapine_types import TypeSystem
            df.inferred_types = TypeSystem.infer_schema(all_rows)
            self.dataframes[name] = df
            self.log_lineage(name, step.source, f"READ {len(files)} FILES")
            print(f"  📂 Read {len(files)} files → {len(all_rows)} rows")
            return df

        if self.use_duckdb and step.format_type in ("csv","json"):
            duck = self._get_duck()
            t = step.alias or f"_t_{len(self.dataframes)}"
            rows, schema = duck.load_csv(step.source, t) if step.format_type=="csv" else duck.load_json(step.source, t)
            name = step.alias or f"_df_{len(self.dataframes)}"
            df = DataFrame(rows, schema, f"read {step.format_type}")
            from dapine_types import TypeSystem
            df.inferred_types = TypeSystem.infer_schema(rows)
            self.dataframes[name] = df
            self.log_lineage(name, step.source, f"READ {step.format_type.upper()}")
            return df
        if step.format_type=="csv":
            try:
                with open(step.source,"r", encoding='utf-8') as f:
                    r = csv.DictReader(f)
                    rows = [{k: self._infer_type(v) for k,v in row.items()} for row in r]
                    schema = list(rows[0].keys()) if rows else []
                    df = DataFrame(rows, schema, f"read csv")
                    from dapine_types import TypeSystem
                    df.inferred_types = TypeSystem.infer_schema(rows)
                    name = step.alias or f"_df_{len(self.dataframes)}"
                    self.dataframes[name] = df
                    self.log_lineage(name, step.source, "READ CSV")
                    return df
            except FileNotFoundError:
                raise RuntimeError(f"File not found: '{step.source}'", step.line)
        elif step.format_type=="json":
            try:
                with open(step.source,"r", encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict): data = [data]
                    rows = data if isinstance(data, list) else []
                    schema = list(rows[0].keys()) if rows else []
                    df = DataFrame(rows, schema, "read json")
                    from dapine_types import TypeSystem
                    df.inferred_types = TypeSystem.infer_schema(rows)
                    name = step.alias or f"_df_{len(self.dataframes)}"
                    self.dataframes[name] = df
                    self.log_lineage(name, step.source, "READ JSON")
                    return df
            except FileNotFoundError:
                raise RuntimeError(f"File not found: '{step.source}'", step.line)
        elif step.format_type=="parquet":
            from connectors import Connectors
            rows, schema = Connectors().read_parquet(step.source)
            name = step.alias or f"_df_{len(self.dataframes)}"
            df = DataFrame(rows, schema, "read parquet")
            from dapine_types import TypeSystem
            df.inferred_types = TypeSystem.infer_schema(rows)
            self.dataframes[name] = df
            self.log_lineage(name, step.source, "READ PARQUET")
            return df
        raise RuntimeError(f"Unsupported: {step.format_type}", step.line)

    def execute_http_read(self, step):
        try:
            with urllib.request.urlopen(step.url) as resp:
                data = json.loads(resp.read().decode())
                rows = data
                if isinstance(rows, dict):
                    if 'results' in rows and isinstance(rows['results'], list): rows = rows['results']
                    elif 'data' in rows and isinstance(rows['data'], list): rows = rows['data']
                    elif 'quotes' in rows and isinstance(rows['quotes'], list): rows = rows['quotes']
                    elif 'products' in rows and isinstance(rows['products'], list): rows = rows['products']
                    elif 'facts' in rows and isinstance(rows['facts'], list): rows = rows['facts']
                    elif 'jokes' in rows and isinstance(rows['jokes'], list): rows = rows['jokes']
                    elif 'breeds' in rows and isinstance(rows['breeds'], list): rows = rows['breeds']
                    else: rows = [rows]
                if isinstance(rows, list) and len(rows) > 0 and isinstance(rows[0], dict):
                    schema = list(rows[0].keys())
                else:
                    schema = ["data"]; rows = [{"data": str(rows)}]
                df = DataFrame(rows, schema, f"http read")
                from dapine_types import TypeSystem
                df.inferred_types = TypeSystem.infer_schema(rows)
                name = step.alias or f"_df_{len(self.dataframes)}"
                self.dataframes[name] = df
                self.log_lineage(name, step.url, "HTTP READ")
                return df
        except Exception as e:
            raise RuntimeError(f"HTTP read failed: {e}", step.line)

    def execute_let(self, step):
        self.variables[step.var_name] = self._eval_atomic(step.value, {})
        return self.variables[step.var_name]

    def execute_filter(self, step):
        step.condition = self._resolve_vars(step.condition)
        df = self.get_df(step.input_ref, step.line)
        prev_count = len(df.rows)
        
        if self.use_duckdb and step.input_ref in self.dataframes:
            try:
                self._df_to_duck(step.input_ref)
                duck = self._get_duck()
                alias = step.alias or f"_t_{len(self.dataframes)}"
                cond = self._condition_to_sql(step.condition)
                duck.conn.execute(f"CREATE OR REPLACE TABLE {alias} AS SELECT * FROM {step.input_ref} WHERE {cond}")
                rows, schema = duck._table_to_rows(alias)
                name = step.alias or f"_df_{len(self.dataframes)}"
                df = DataFrame(rows, schema, "filter")
                if hasattr(self.get_df(step.input_ref), 'inferred_types'):
                    df.inferred_types = self.get_df(step.input_ref).inferred_types
                self.dataframes[name] = df
                new_count = len(rows)
                if new_count == 0 and prev_count > 0:
                    print(f"  ⚠️  Filter removed ALL {prev_count} rows! Check your conditions.")
                self.log_lineage(name, step.input_ref, "FILTER")
                return df
            except: pass
        
        filtered = [row for row in df.rows if self.eval_condition(step.condition, row)]
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(filtered, df.schema, "filter")
        if hasattr(df, 'inferred_types'): ndf.inferred_types = df.inferred_types
        self.dataframes[name] = ndf
        
        new_count = len(filtered)
        if new_count == 0 and prev_count > 0:
            print(f"  ⚠️  Filter removed ALL {prev_count} rows! Check your conditions.")
        
        self.log_lineage(name, step.input_ref, "FILTER")
        return ndf

    def _condition_to_sql(self, expr):
        if isinstance(expr, BinaryOp):
            l = self._sql_val(expr.left); r = self._sql_val(expr.right)
            m = {"==":"=", "!=":"<>", "and":"AND", "or":"OR", ">":">", "<":"<", ">=":">=", "<=":"<="}
            return f"({l} {m.get(expr.op, expr.op.upper())} {r})"
        return "1=1"

    def _sql_val(self, expr):
        if isinstance(expr, Identifier): return f'"{expr.name}"'
        if isinstance(expr, ColumnRef): return f'"{expr.column}"'
        if isinstance(expr, StringLiteral): return f"'{expr.value}'"
        if isinstance(expr, NumberLiteral): return str(expr.value)
        if isinstance(expr, BooleanLiteral): return "TRUE" if expr.value else "FALSE"
        if isinstance(expr, NullLiteral): return "NULL"
        return "NULL"

    def execute_select(self, step):
        df = self.get_df(step.input_ref, step.line)
        if len(df.rows) == 0:
            name = step.alias or f"_df_{len(self.dataframes)}"
            empty_df = DataFrame([], step.columns, "select")
            self.dataframes[name] = empty_df
            return empty_df
        for c in step.columns: self.check_column(df, c, step.line)
        rows = [{c: row.get(c) for c in step.columns} for row in df.rows]
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, step.columns, "select")
        from dapine_types import TypeSystem
        ndf.inferred_types = {c: TypeSystem.infer_column(rows, c) for c in step.columns}
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"SELECT")
        return ndf

    def execute_join(self, step):
        l = self.get_df(step.left_ref, step.line); r = self.get_df(step.right_ref, step.line)
        joined = []
        for lr in l.rows:
            m = False
            for rr in r.rows:
                if lr.get(step.on_column) == rr.get(step.on_column): joined.append({**lr, **rr}); m = True
            if step.join_type=="left" and not m: joined.append({**lr, **{k: None for k in r.schema}})
        name = step.alias or f"_df_{len(self.dataframes)}"
        schema = l.schema + [c for c in r.schema if c not in l.schema]
        ndf = DataFrame(joined, schema, "join")
        self.dataframes[name] = ndf
        self.log_lineage(name, f"{step.left_ref},{step.right_ref}", f"JOIN")
        return ndf

    def execute_group(self, step):
        df = self.get_df(step.input_ref, step.line)
        if len(df.rows) == 0:
            name = step.alias or f"_df_{len(self.dataframes)}"
            schema = [step.key_column] + [a.output_name for a in step.aggregations]
            empty_df = DataFrame([], schema, "group")
            self.dataframes[name] = empty_df
            return empty_df
        self.check_column(df, step.key_column, step.line)
        groups = {}
        for row in df.rows:
            k = row.get(step.key_column)
            if k not in groups: groups[k] = []
            groups[k].append(row)
        result = []
        for k, rows in groups.items():
            out = {step.key_column: k}
            for agg in step.aggregations:
                if agg.func=="count": out[agg.output_name] = len(rows)
                else:
                    vals = [float(r.get(agg.column)) for r in rows if r.get(agg.column) is not None]
                    if agg.func=="sum": out[agg.output_name] = sum(vals)
                    elif agg.func=="avg": out[agg.output_name] = sum(vals)/len(vals) if vals else 0
                    elif agg.func=="min": out[agg.output_name] = min(vals) if vals else None
                    elif agg.func=="max": out[agg.output_name] = max(vals) if vals else None
            result.append(out)
        name = step.alias or f"_df_{len(self.dataframes)}"
        schema = [step.key_column] + [a.output_name for a in step.aggregations]
        ndf = DataFrame(result, schema, "group")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"GROUP BY {step.key_column}")
        return ndf

    def execute_write(self, step):
        df = self.get_df(step.input_ref, step.line)
        if step.format_type=="csv":
            with open(step.target,"w",newline="", encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=df.schema); w.writeheader(); w.writerows(df.rows)
        elif step.format_type=="json":
            with open(step.target,"w", encoding='utf-8') as f: json.dump(df.rows, f, indent=2, default=str)
        elif step.format_type=="parquet":
            from connectors import Connectors
            Connectors().write_parquet(df.rows, df.schema, step.target)
        self.log_lineage(step.target, step.input_ref, f"WRITE")
        print(f"Written {len(df.rows)} rows to {step.target}")

    def execute_sort(self, step):
        df = self.get_df(step.input_ref, step.line)
        if len(df.rows) == 0:
            name = step.alias or f"_df_{len(self.dataframes)}"
            empty_df = DataFrame([], df.schema, "sort")
            self.dataframes[name] = empty_df
            return empty_df
        self.check_column(df, step.column, step.line)
        rev = step.direction=="desc"
        rows = sorted(df.rows, key=lambda r: (r.get(step.column) is None, r.get(step.column,"")), reverse=rev)
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, df.schema, "sort")
        if hasattr(df, 'inferred_types'): ndf.inferred_types = df.inferred_types
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"SORT")
        return ndf

    def execute_distinct(self, step):
        df = self.get_df(step.input_ref, step.line)
        seen = set(); uniq = []
        for row in df.rows:
            key = tuple(sorted(str(v) for v in row.items()))
            if key not in seen: seen.add(key); uniq.append(row)
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(uniq, df.schema, "distinct")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, "DISTINCT")
        return ndf

    def execute_limit(self, step):
        df = self.get_df(step.input_ref, step.line)
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(df.rows[:step.count], df.schema, "limit")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"LIMIT")
        return ndf

    def execute_mutate(self, step):
        df = self.get_df(step.input_ref, step.line)
        if len(df.rows) == 0:
            name = step.alias or f"_df_{len(self.dataframes)}"
            empty_df = DataFrame([], df.schema + [step.new_column], "mutate")
            self.dataframes[name] = empty_df
            self.log_lineage(name, step.input_ref, f"MUTATE add {step.new_column} (empty)")
            return empty_df
        mutated = []
        for row in df.rows:
            new_row = dict(row)
            try: new_row[step.new_column] = self.eval_arithmetic(step.expression, row)
            except: new_row[step.new_column] = None
            mutated.append(new_row)
        name = step.alias or f"_df_{len(self.dataframes)}"
        schema = df.schema + [step.new_column]
        ndf = DataFrame(mutated, schema, f"mutate add {step.new_column}")
        if hasattr(df, 'inferred_types'):
            ndf.inferred_types = dict(df.inferred_types)
            ndf.inferred_types[step.new_column] = 'float'
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"MUTATE add {step.new_column}")
        return ndf

    def execute_union(self, step):
        l = self.get_df(step.left_ref, step.line); r = self.get_df(step.right_ref, step.line)
        schema = list(dict.fromkeys(l.schema + r.schema))
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(l.rows + r.rows, schema, "union")
        self.dataframes[name] = ndf
        self.log_lineage(name, f"{step.left_ref},{step.right_ref}", "UNION")
        return ndf

    def execute_rename(self, step):
        df = self.get_df(step.input_ref, step.line)
        rows = [{step.renames.get(k,k): v for k,v in row.items()} for row in df.rows]
        schema = [step.renames.get(c,c) for c in df.schema]
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, schema, "rename")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"RENAME")
        return ndf

    def execute_print(self, step):
        df = self.get_df(step.input_ref, step.line)
        if len(df.rows) == 0:
            print(f"\n  {step.input_ref}: EMPTY (0 rows)")
            if hasattr(df, 'inferred_types') and df.inferred_types:
                print(f"  Expected types: {', '.join(f'{k}:{v}' for k,v in df.inferred_types.items())}")
            print(f"  {'-'*50}\n")
            return df
        print(f"\n  {step.input_ref}: {len(df.rows)} rows x {len(df.schema)} cols")
        print(f"  Columns: {', '.join(df.schema)}")
        if hasattr(df, 'inferred_types') and df.inferred_types:
            print(f"  Types: {', '.join(f'{k}:{v}' for k,v in df.inferred_types.items())}")
        print(f"  {'-'*50}")
        for row in df.rows[:20]: print(f"  {row}")
        if len(df.rows)>20: print(f"  ... and {len(df.rows)-20} more")
        print(f"  {'-'*50}\n")
        return df

    def execute_cast(self, step):
        df = self.get_df(step.input_ref, step.line)
        for row in df.rows:
            v = row.get(step.column)
            try:
                if step.new_type=="int": row[step.column] = int(float(v)) if v is not None else None
                elif step.new_type=="float": row[step.column] = float(v) if v is not None else None
                elif step.new_type=="string": row[step.column] = str(v) if v is not None else ""
                elif step.new_type=="bool": row[step.column] = bool(v)
            except: pass
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(list(df.rows), df.schema, "cast")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"CAST")
        return ndf

    def execute_sample(self, step):
        df = self.get_df(step.input_ref, step.line)
        k = max(1, int(len(df.rows)*step.percent/100))
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(random.sample(df.rows, min(k, len(df.rows))), df.schema, "sample")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"SAMPLE")
        return ndf

    def execute_stats(self, step):
        df = self.get_df(step.input_ref, step.line)
        print(f"\n  STATS: {step.input_ref} ({len(df.rows)} rows)")
        print(f"  {'-'*50}")
        for col in df.schema:
            vals = [r.get(col) for r in df.rows if isinstance(r.get(col), (int, float))]
            if vals:
                if len(vals)>1: print(f"  {col}: min={min(vals)}, max={max(vals)}, mean={statistics.mean(vals):.2f}, median={statistics.median(vals):.2f}, stdev={statistics.stdev(vals):.2f}")
                else: print(f"  {col}: value={vals[0]}")
            else: print(f"  {col}: (non-numeric)")
        print(f"  {'-'*50}\n")
        return df

    def execute_for(self, step):
        df = self.get_df(step.input_ref, step.line)
        for row in df.rows: self.variables[step.row_var] = row; [self.execute_step(s) for s in step.body]
        return df

    def execute_case(self, step):
        df = self.get_df(step.input_ref, step.line)
        for row in df.rows:
            v = row.get(step.column); matched = False
            for case in step.cases:
                if v == self._eval_atomic(case.value, row):
                    matched = True; [self.execute_step(s) for s in case.body]; break
            if not matched and step.default_alias: [self.execute_step(s) for s in step.default_alias]
        return df

    def execute_if(self, step):
        if self.eval_condition(step.condition, {}): [self.execute_step(s) for s in step.if_body]
        elif step.else_body: [self.execute_step(s) for s in step.else_body]
        return None

    def execute_chart(self, step):
        from charts import ChartEngine
        ChartEngine(self).generate_chart(step.input_ref, step.chart_type, step.label_col, step.value_col, step.title, step.target)
        return None

    def execute_train(self, step):
        from ml_engine import MLEngine
        if not self.ml_engine: self.ml_engine = MLEngine()
        df = self.get_df(step.input_ref, step.line)
        r = self.ml_engine.train(df, step.target_col, step.model_type, step.model_name)
        print(f"\n  Model: {step.model_name} | R2: {r.get('metrics',{}).get('r2','N/A')}")
        return None

    def execute_predict(self, step):
        from ml_engine import MLEngine
        if not self.ml_engine: self.ml_engine = MLEngine()
        df = self.get_df(step.input_ref, step.line)
        rows, schema = self.ml_engine.predict(df, step.model_name, step.output_col)
        if rows is None: print(f"Error: {schema.get('error')}"); return None
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, schema, "predict")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.input_ref, f"PREDICT")
        return ndf

    def execute_db_read(self, step):
        from connectors import Connectors
        rows, cols = Connectors().read_database(step.connection_string, step.query, step.alias)
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, cols, "db read")
        self.dataframes[name] = ndf
        self.log_lineage(name, "database", "DB READ")
        return ndf

    def execute_db_write(self, step):
        from connectors import Connectors
        df = self.get_df(step.input_ref, step.line)
        Connectors().write_database(df.rows, df.schema, step.connection_string, step.table_name)
        print(f"Written {len(df.rows)} rows to DB table '{step.table_name}'")

    def execute_excel_read(self, step):
        from connectors import Connectors
        rows, cols = Connectors().read_excel(step.source, step.sheet_name)
        name = step.alias or f"_df_{len(self.dataframes)}"
        ndf = DataFrame(rows, cols, "excel read")
        self.dataframes[name] = ndf
        self.log_lineage(name, step.source, "EXCEL READ")
        return ndf

    def execute_excel_write(self, step):
        from connectors import Connectors
        df = self.get_df(step.input_ref, step.line)
        Connectors().write_excel(df.rows, df.schema, step.target, step.sheet_name)
        print(f"Written {len(df.rows)} rows to {step.target}")

    def execute_report(self, step):
        from reports import ReportEngine
        ReportEngine(self).generate_report(step.input_ref, step.title, step.target)
        return None

    def execute_alert(self, step):
        from alerts import AlertEngine
        AlertEngine(self.slack_webhook).slack(step.message, step.title)
        return None

    def _infer_type(self, v):
        v = v.strip()
        if v=="" or v.lower() in ("null","none"): return None
        if v.lower()=="true": return True
        if v.lower()=="false": return False
        try: return int(v)
        except: pass
        try: return float(v)
        except: pass
        return v

    def _eval_atomic(self, expr, row):
        if isinstance(expr, BinaryOp): return self.eval_condition(expr, row)
        if isinstance(expr, ArithOp): return self.eval_arithmetic(expr, row)
        if isinstance(expr, FuncCall): return self._eval_func(expr, row)
        if isinstance(expr, ColumnRef): return row.get(expr.column)
        if isinstance(expr, Identifier):
            if expr.name in self.variables: return self.variables[expr.name]
            if expr.name in self.functions: return self.functions[expr.name]
            return row.get(expr.name)
        if isinstance(expr, StringLiteral): return expr.value
        if isinstance(expr, NumberLiteral): return expr.value
        if isinstance(expr, BooleanLiteral): return expr.value
        if isinstance(expr, NullLiteral): return None
        return None

    def _eval_func(self, expr, row):
        if expr.name in self.functions:
            f = self.functions[expr.name]; saved = dict(self.variables)
            for i,p in enumerate(f.params):
                if i < len(expr.args): self.variables[p] = self._eval_atomic(expr.args[i], row)
            res = self._eval_atomic(f.body_expr, row); self.variables = saved; return res
        args = [self._eval_atomic(a, row) for a in expr.args]
        if expr.name=="upper": return str(args[0]).upper() if args[0] is not None else ""
        if expr.name=="lower": return str(args[0]).lower() if args[0] is not None else ""
        if expr.name=="length": return len(str(args[0])) if args[0] is not None else 0
        if expr.name=="trim": return str(args[0]).strip() if args[0] is not None else ""
        if expr.name=="concat": return "".join(str(a) for a in args)
        if expr.name=="abs": return abs(args[0]) if args[0] is not None else None
        if expr.name=="round": return round(args[0], args[1] if len(args)>1 else 0) if args[0] is not None else None
        if expr.name=="ceil": return math.ceil(args[0]) if args[0] is not None else None
        if expr.name=="floor": return math.floor(args[0]) if args[0] is not None else None
        if expr.name=="sqrt": return math.sqrt(args[0]) if args[0] is not None and args[0]>=0 else None
        if expr.name=="today": return date.today()
        return None

    def eval_condition(self, expr, row):
        if isinstance(expr, BinaryOp):
            l = self._eval_atomic(expr.left, row); r = self._eval_atomic(expr.right, row)
            if expr.op=="contains": return str(r) in str(l) if l and r else False
            if expr.op=="starts_with": return str(l).startswith(str(r)) if l and r else False
            if expr.op=="ends_with": return str(l).endswith(str(r)) if l and r else False
            if expr.op=="is": return l is None
            if expr.op=="is_not": return l is not None
            if l is None and r is None: return expr.op=="=="
            if l is None or r is None: return expr.op=="!="
            l, r = self._coerce(l, r)
            ops = {"==": lambda a,b: a==b, "!=": lambda a,b: a!=b, ">": lambda a,b: a>b,
                   "<": lambda a,b: a<b, ">=": lambda a,b: a>=b, "<=": lambda a,b: a<=b,
                   "and": lambda a,b: a and b, "or": lambda a,b: a or b}
            if expr.op in ops: return ops[expr.op](l, r)
        return self._eval_atomic(expr, row)

    def eval_arithmetic(self, expr, row):
        if isinstance(expr, ArithOp):
            l = self._eval_atomic(expr.left, row) or 0
            r = self._eval_atomic(expr.right, row) or 0
            if expr.op=="+": return str(l)+str(r) if isinstance(l,str) or isinstance(r,str) else l+r
            if expr.op=="-": return l - r
            if expr.op=="*": return l * r
            if expr.op=="/": return l / r if r!=0 else None
        return self._eval_atomic(expr, row)

    def _coerce(self, l, r):
        if isinstance(l, str) and isinstance(r, (int, float)):
            try: l = float(l)
            except: pass
        elif isinstance(r, str) and isinstance(l, (int, float)):
            try: r = float(r)
            except: pass
        return l, r