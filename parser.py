from ast_nodes import *
from errors import ParserError
from datetime import date

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.functions = {}

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type=None):
        token = self.peek()
        if token is None:
            raise ParserError("Unexpected end of input")
        if expected_type and token.type != expected_type:
            raise ParserError(f"Expected {expected_type}, got {token.type} ('{token.value}')", token.line, token.column)
        self.pos += 1
        return token

    def is_keyword_or_identifier(self, token):
        return token and token.type not in ("EOF","LBRACE","RBRACE","LPAREN","RPAREN","LBRACKET","RBRACKET",
            "COMMA","COLON","DOT","ASSIGN","PLUS","MINUS","STAR","SLASH","PERCENT","ARROW",
            "EQ","NEQ","GT","LT","GTE","LTE","STRING_LIT","NUMBER_LIT","DATE_LIT")

    def parse(self):
        statements = []
        while self.peek() and self.peek().type != "EOF":
            if self.peek().type == "PIPELINE": statements.append(self.parse_pipeline())
            elif self.peek().type == "IMPORT": statements.append(self.parse_import())
            elif self.peek().type == "FUNC": self.parse_function()
            elif self.peek().type == "DEFINE": statements.append(self.parse_define())
            else:
                t = self.peek()
                raise ParserError(f"Unexpected: {t.type}", t.line, t.column)
        return Program(statements)

    def parse_function(self):
        line = self.peek().line
        self.consume("FUNC")
        name = self.consume("IDENTIFIER").value
        self.consume("LPAREN")
        params = []
        if self.peek().type != "RPAREN":
            pname = self.consume("IDENTIFIER").value
            pdefault = None
            if self.peek() and self.peek().type == "ASSIGN":
                self.consume("ASSIGN"); pdefault = self.parse_primary()
            params.append(Param(pname, None, pdefault))
            while self.peek().type == "COMMA":
                self.consume("COMMA")
                pname = self.consume("IDENTIFIER").value
                pdefault = None
                if self.peek() and self.peek().type == "ASSIGN":
                    self.consume("ASSIGN"); pdefault = self.parse_primary()
                params.append(Param(pname, None, pdefault))
        self.consume("RPAREN")
        self.consume("ASSIGN")
        body = self.parse_expression()
        self.functions[name] = FuncDef(name, params, body, line)

    def parse_pipeline(self):
        self.consume("PIPELINE")
        name = self.consume("IDENTIFIER").value
        self.consume("LPAREN")
        self.consume("RPAREN")
        self.consume("LBRACE")
        steps = self.parse_steps()
        self.consume("RBRACE")
        return Pipeline(name, [], steps, self.peek().line if self.peek() else 0)

    def parse_steps(self):
        steps = []
        while self.peek() and self.peek().type != "RBRACE":
            steps.append(self.parse_step())
        return steps

    def parse_step(self):
        t = self.peek()
        type_map = {
            "READ": self.parse_read, "HTTP": self.parse_http_read, "WRITE": self.parse_write,
            "FILTER": self.parse_filter, "SELECT": self.parse_select, "SORT": self.parse_sort,
            "LIMIT": self.parse_limit, "MUTATE": self.parse_mutate, "RENAME": self.parse_rename,
            "CAST": self.parse_cast, "SAMPLE": self.parse_sample, "DISTINCT": self.parse_distinct,
            "GROUP": self.parse_group, "JOIN": self.parse_join, "UNION": self.parse_union,
            "PRINT": self.parse_print, "STATS": self.parse_stats, "CHART": self.parse_chart,
            "REPORT": self.parse_report, "LET": self.parse_let, "IF": self.parse_if,
            "FOR": self.parse_for, "TRAIN": self.parse_train, "PREDICT": self.parse_predict,
            "EXCEL": self.parse_excel, "ALERT": self.parse_alert,
            "TRY": self.parse_try, "PIVOT": self.parse_pivot, "EXPORT": self.parse_export,
            "EMAIL": self.parse_email, "SLACK": self.parse_slack, "UPLOAD": self.parse_s3,
            "RANK": self.parse_window,
        }
        if t.type in type_map: return type_map[t.type]()
        raise ParserError(f"Unknown: {t.value}", t.line, t.column)

    def parse_read(self):
        line = self.peek().line
        self.consume("READ")
        source = self.consume("STRING_LIT").value.strip('"')
        fmt = "csv"
        if source.endswith(".json"): fmt = "json"
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            n = self.peek()
            if n and n.value in ("csv","json","parquet"): fmt = self.consume().value
            else: alias = n.value; self.consume()
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return ReadStep(source, fmt, {}, alias, line)

    def parse_http_read(self):
        line = self.peek().line
        self.consume("HTTP"); self.consume("READ")
        url = self.consume("STRING_LIT").value.strip('"')
        fmt = "json"
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); fmt = self.consume().value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return HttpReadStep(url, fmt, alias, line)

    def parse_write(self):
        line = self.peek().line
        self.consume("WRITE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')
        fmt = "csv"
        if target.endswith(".json"): fmt = "json"
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); fmt = self.consume().value
        return WriteStep(input_ref, target, fmt, None, line)

    def parse_filter(self):
        line = self.peek().line
        self.consume("FILTER")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("WHERE")
        cond = self.parse_expression()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return FilterStep(input_ref, cond, alias, line)

    def parse_select(self):
        line = self.peek().line
        self.consume("SELECT")
        cols = []
        if self.is_keyword_or_identifier(self.peek()): cols.append(self.consume().value)
        while self.peek().type == "COMMA":
            self.consume("COMMA"); cols.append(self.consume().value)
        self.consume("FROM")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return SelectStep(input_ref, cols, alias, line)

    def parse_sort(self):
        line = self.peek().line
        self.consume("SORT")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("BY")
        col = self.peek().value; self.consume()
        direction = "asc"
        if self.peek() and self.peek().type in ("ASC","DESC"): direction = self.consume().value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return SortStep(input_ref, col, direction, alias, line)

    def parse_limit(self):
        line = self.peek().line
        self.consume("LIMIT")
        input_ref = self.consume("IDENTIFIER").value
        count = int(self.consume("NUMBER_LIT").value)
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return LimitStep(input_ref, count, alias, line)

    def parse_mutate(self):
        line = self.peek().line
        self.consume("MUTATE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("ADD")
        new_col = self.peek().value; self.consume()
        self.consume("ASSIGN")
        expr = self.parse_arithmetic()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return MutateStep(input_ref, new_col, expr, alias, line)

    def parse_rename(self):
        line = self.peek().line
        self.consume("RENAME")
        input_ref = self.consume("IDENTIFIER").value
        renames = {}
        old = self.peek().value; self.consume()
        self.consume("TO")
        new = self.peek().value; self.consume()
        renames[old] = new
        while self.peek().type == "COMMA":
            self.consume("COMMA"); old = self.peek().value; self.consume()
            self.consume("TO"); new = self.peek().value; self.consume()
            renames[old] = new
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return RenameStep(input_ref, renames, alias, line)

    def parse_cast(self):
        line = self.peek().line
        self.consume("CAST")
        input_ref = self.consume("IDENTIFIER").value
        col = self.consume("IDENTIFIER").value
        self.consume("AS")
        new_type = self.peek().value; self.consume()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return CastStep(input_ref, col, new_type, alias, line)

    def parse_sample(self):
        line = self.peek().line
        self.consume("SAMPLE")
        input_ref = self.consume("IDENTIFIER").value
        pct = float(self.consume("NUMBER_LIT").value)
        if self.peek().type == "PERCENT": self.consume("PERCENT")
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return SampleStep(input_ref, pct, alias, line)

    def parse_distinct(self):
        line = self.peek().line
        self.consume("DISTINCT")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return DistinctStep(input_ref, alias, line)

    def parse_group(self):
        line = self.peek().line
        self.consume("GROUP")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("BY")
        key = self.consume("IDENTIFIER").value
        self.consume("LBRACKET")
        aggs = []
        while self.peek().type != "RBRACKET":
            func = self.consume().value
            self.consume("LPAREN"); col = self.consume("IDENTIFIER").value; self.consume("RPAREN")
            self.consume("AS"); out = self.consume("IDENTIFIER").value
            aggs.append(Aggregation(func, col, out))
            if self.peek().type == "COMMA": self.consume("COMMA")
        self.consume("RBRACKET")
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return GroupStep(input_ref, key, aggs, alias, line)

    def parse_join(self):
        line = self.peek().line
        jt = "inner"
        if self.peek().type in ("INNER","LEFT","RIGHT"): jt = self.consume().value
        self.consume("JOIN")
        left = self.consume("IDENTIFIER").value
        self.consume("WITH")
        right = self.consume("IDENTIFIER").value
        self.consume("ON")
        on_col = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return JoinStep(left, right, on_col, jt, alias, line)

    def parse_union(self):
        line = self.peek().line
        self.consume("UNION")
        left = self.consume("IDENTIFIER").value
        self.consume("WITH")
        right = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return UnionStep(left, right, alias, line)

    def parse_print(self):
        line = self.peek().line
        self.consume("PRINT")
        return PrintStep(self.consume("IDENTIFIER").value, line)

    def parse_stats(self):
        line = self.peek().line
        self.consume("STATS")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return StatsStep(input_ref, alias, line)

    def parse_chart(self):
        line = self.peek().line
        self.consume("CHART")
        input_ref = self.consume("IDENTIFIER").value
        val_col = self.consume("IDENTIFIER").value
        self.consume("BY")
        lbl_col = self.consume("IDENTIFIER").value
        self.consume("AS")
        chart_type = self.peek().value; self.consume()
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')
        return ChartStep(input_ref, chart_type, lbl_col, val_col, f"chart", target, None, line)

    def parse_report(self):
        line = self.peek().line
        self.consume("REPORT")
        input_ref = self.peek().value; self.consume()
        self.consume("AS")
        title = self.consume("STRING_LIT").value.strip('"')
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')
        return ReportStep(input_ref, title, target, None, line)

    def parse_let(self):
        line = self.peek().line
        self.consume("LET")
        var_name = self.consume("IDENTIFIER").value
        var_type = None
        if self.peek() and self.peek().type == "COLON":
            self.consume("COLON"); var_type = self.peek().value; self.consume()
        self.consume("ASSIGN")
        value = self.parse_expression()
        return LetStep(var_name, var_type, value, None, line)

    def parse_if(self):
        line = self.peek().line
        self.consume("IF")
        cond = self.parse_expression()
        self.consume("LBRACE"); if_body = self.parse_steps(); self.consume("RBRACE")
        else_body = []
        if self.peek() and self.peek().type == "ELSE":
            self.consume("ELSE"); self.consume("LBRACE"); else_body = self.parse_steps(); self.consume("RBRACE")
        return IfStep(cond, if_body, else_body, None, line)

    def parse_for(self):
        line = self.peek().line
        self.consume("FOR")
        row_var = self.consume("IDENTIFIER").value
        self.consume("IN")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("LBRACE"); body = self.parse_steps(); self.consume("RBRACE")
        return ForStep(row_var, input_ref, body, None, line)

    def parse_train(self):
        line = self.peek().line
        self.consume("TRAIN")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("PREDICT")
        target = self.consume("IDENTIFIER").value
        self.consume("USING")
        model_type = self.peek().value; self.consume()
        self.consume("AS")
        model_name = self.consume("IDENTIFIER").value
        return TrainStep(input_ref, target, model_type, model_name, None, line)

    def parse_predict(self):
        line = self.peek().line
        self.consume("PREDICT")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("USING")
        model_name = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return PredictStep(input_ref, model_name, "prediction", alias, line)

    def parse_excel(self):
        line = self.peek().line
        self.consume("EXCEL")
        if self.peek().type == "READ":
            self.consume("READ"); source = self.consume("STRING_LIT").value.strip('"')
            alias = None
            if self.peek() and self.peek().type == "AS":
                self.consume("AS"); alias = self.consume("IDENTIFIER").value
            return ExcelReadStep(source, None, alias, line)
        self.consume("WRITE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')
        return ExcelWriteStep(input_ref, target, "Sheet1", None, line)

    def parse_alert(self):
        line = self.peek().line
        self.consume("ALERT")
        msg = self.consume("STRING_LIT").value.strip('"')
        title = "Dapine Alert"
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); title = self.consume("STRING_LIT").value.strip('"')
        return AlertStep(msg, title, line)

    def parse_import(self):
        line = self.peek().line
        self.consume("IMPORT")
        return ImportStep(self.consume("STRING_LIT").value.strip('"'), line)

    # ============ NEW FEATURES ============

    def parse_try(self):
        line = self.peek().line
        self.consume("TRY"); self.consume("LBRACE")
        try_body = self.parse_steps()
        self.consume("RBRACE"); self.consume("CATCH"); self.consume("LBRACE")
        catch_body = self.parse_steps()
        self.consume("RBRACE")
        return TryStep(try_body, catch_body, None, line)

    def parse_pivot(self):
        line = self.peek().line
        self.consume("PIVOT")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("ROWS"); self.consume("TO"); self.consume("COLUMNS"); self.consume("BY")
        key_col = self.consume("IDENTIFIER").value
        agg_func = "sum"
        if self.peek().type in ("SUM","COUNT","AVG","MIN","MAX"): agg_func = self.consume().value
        value_col = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return PivotStep(input_ref, key_col, value_col, agg_func, alias, line)

    def parse_define(self):
        line = self.peek().line
        self.consume("DEFINE")
        name = self.consume("IDENTIFIER").value
        self.consume("AS"); self.consume("LPAREN")
        body = self.parse_steps()
        self.consume("RPAREN")
        return CTEStep(name, body, line)

    def parse_export(self):
        line = self.peek().line
        self.consume("EXPORT")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("AS")
        fmt = self.peek().value; self.consume()
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')
        return ExportStep(input_ref, fmt, target, None, line)

    def parse_email(self):
        line = self.peek().line
        self.consume("EMAIL")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("TO")
        to_addr = self.consume("STRING_LIT").value.strip('"')
        subject = "Dapine Report"
        if self.peek() and self.peek().type == "STRING_LIT":
            subject = self.consume("STRING_LIT").value.strip('"')
        return EmailStep(input_ref, to_addr, subject, None, line)

    def parse_slack(self):
        line = self.peek().line
        self.consume("SLACK")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("TO")
        channel = self.consume("STRING_LIT").value.strip('"')
        return SlackStep(input_ref, channel, None, line)

    def parse_s3(self):
        line = self.peek().line
        self.consume("UPLOAD")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("TO")
        path = self.consume("STRING_LIT").value.strip('"')
        return S3Step(input_ref, path, None, line)

    def parse_window(self):
        line = self.peek().line
        func = self.peek().value; self.consume()
        self.consume("LPAREN"); col = self.consume("IDENTIFIER").value; self.consume("RPAREN")
        self.consume("OVER")
        partition_by = None; order_by = None
        if self.peek().type == "PARTITION":
            self.consume("PARTITION"); self.consume("BY"); partition_by = self.consume("IDENTIFIER").value
        if self.peek().type == "ORDER":
            self.consume("ORDER"); self.consume("BY"); order_by = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS"); alias = self.consume("IDENTIFIER").value
        return WindowStep(None, func, col, partition_by, order_by, alias, line)

    # ============ EXPRESSIONS ============

    def parse_expression(self):
        left = self.parse_arithmetic()
        if self.peek() and self.peek().type in ("EQ","NEQ","GT","LT","GTE","LTE","AND","OR","MATCHES","CONTAINS","STARTS_WITH","ENDS_WITH"):
            op = self.consume().value
            return BinaryOp(left, op, self.parse_expression())
        return left

    def parse_arithmetic(self):
        left = self.parse_primary()
        while self.peek() and self.peek().type in ("PLUS","MINUS","STAR","SLASH"):
            op = self.consume().value
            left = ArithOp(left, op, self.parse_primary())
        return left

    def parse_primary(self):
        t = self.peek()
        if t.type == "STRING_LIT": self.consume(); return StringLiteral(t.value.strip('"'))
        if t.type == "NUMBER_LIT": self.consume(); return NumberLiteral(float(t.value) if "." in t.value else int(t.value))
        if t.type == "TRUE": self.consume(); return BooleanLiteral(True)
        if t.type == "FALSE": self.consume(); return BooleanLiteral(False)
        if t.type == "NULL": self.consume(); return NullLiteral()
        if t.type == "DATE_LIT":
            self.consume()
            try: return DateLiteral(date.fromisoformat(t.value.strip('#')))
            except: raise ParserError("Invalid date", t.line, t.column)
        if t.type in ("UPPER","LOWER","LENGTH","TRIM","ABS","ROUND","CEIL","FLOOR","SQRT","TODAY","NOW","YEAR","MONTH","DAY","POW","CONCAT"):
            func = self.consume().value
            self.consume("LPAREN"); args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expression())
                while self.peek().type == "COMMA": self.consume("COMMA"); args.append(self.parse_expression())
            self.consume("RPAREN")
            return FuncCall(func, args, t.line)
        if t.type == "IDENTIFIER":
            self.consume()
            if self.peek() and self.peek().type == "DOT":
                self.consume("DOT"); col = self.consume("IDENTIFIER").value
                return ColumnRef(t.value, col)
            if self.peek() and self.peek().type == "LPAREN":
                self.consume("LPAREN"); args = []
                if self.peek().type != "RPAREN":
                    args.append(self.parse_expression())
                    while self.peek().type == "COMMA": self.consume("COMMA"); args.append(self.parse_expression())
                self.consume("RPAREN")
                return FuncCall(t.value, args, t.line)
            return Identifier(t.value)
        if t.type == "LPAREN":
            self.consume("LPAREN"); expr = self.parse_expression(); self.consume("RPAREN")
            return expr
        if t.type == "LBRACKET":
            self.consume("LBRACKET"); elements = []
            if self.peek().type != "RBRACKET":
                elements.append(self.parse_expression())
                while self.peek().type == "COMMA": self.consume("COMMA"); elements.append(self.parse_expression())
            self.consume("RBRACKET")
            return ArrayLiteral(elements)
        raise ParserError(f"Unexpected: {t.type}", t.line, t.column)