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
            raise ParserError("Unexpected end of input", hint="The file might be incomplete")
        if expected_type and token.type != expected_type:
            raise ParserError(
                f"Expected {expected_type}, got {token.type} ('{token.value}')",
                token.line, token.column,
                hint=f"Try replacing '{token.value}' with a {expected_type.lower()}"
            )
        self.pos += 1
        return token

    def is_type_token(self, token):
        return token and token.type in ("TABLE", "INT", "STRING", "FLOAT", "BOOL", "DATE", "IDENTIFIER")

    def is_keyword_or_identifier(self, token):
        return token and token.type not in ("EOF", "LBRACE", "RBRACE", "LPAREN", "RPAREN",
            "LBRACKET", "RBRACKET", "COMMA", "COLON", "DOT", "ASSIGN",
            "PLUS", "MINUS", "STAR", "SLASH", "PERCENT", "ARROW",
            "EQ", "NEQ", "GT", "LT", "GTE", "LTE", "STRING_LIT", "NUMBER_LIT",
            "DATE_LIT", "SEMICOLON")

    def parse(self):
        statements = []
        while self.peek() and self.peek().type != "EOF":
            if self.peek().type == "PIPELINE":
                statements.append(self.parse_pipeline())
            elif self.peek().type == "IMPORT":
                statements.append(self.parse_import())
            elif self.peek().type == "FUNC":
                self.parse_function()
            else:
                token = self.peek()
                raise ParserError(
                    f"Unexpected token: {token.type} ('{token.value}')",
                    token.line, token.column,
                    hint="Expected 'pipeline', 'import', or 'func'"
                )
        return Program(statements)

    def parse_function(self):
        line = self.peek().line
        self.consume("FUNC")
        name = self.consume("IDENTIFIER").value
        self.consume("LPAREN")
        params = []
        if self.peek().type != "RPAREN":
            params.append(self.consume("IDENTIFIER").value)
            while self.peek().type == "COMMA":
                self.consume("COMMA")
                params.append(self.consume("IDENTIFIER").value)
        self.consume("RPAREN")
        self.consume("ASSIGN")
        body = self.parse_expression()
        self.functions[name] = FuncDef(name, params, body, line)

    def parse_pipeline(self):
        self.consume("PIPELINE")
        name = self.consume("IDENTIFIER").value
        params = self.parse_params()
        self.consume("LBRACE")
        steps = self.parse_steps()
        self.consume("RBRACE")
        return Pipeline(name, params, steps, self.peek().line if self.peek() else 0)

    def parse_params(self):
        params = []
        self.consume("LPAREN")
        if self.peek().type != "RPAREN":
            name = self.consume("IDENTIFIER").value
            self.consume("COLON")
            if self.is_type_token(self.peek()):
                ptype = self.consume().value
            else:
                raise ParserError(f"Expected type, got {self.peek().type}", self.peek().line, self.peek().column,
                                hint="Valid types: table, int, string, float, bool, date")
            params.append(Param(name, ptype))
            while self.peek().type == "COMMA":
                self.consume("COMMA")
                name = self.consume("IDENTIFIER").value
                self.consume("COLON")
                if self.is_type_token(self.peek()):
                    ptype = self.consume().value
                else:
                    raise ParserError(f"Expected type, got {self.peek().type}", self.peek().line, self.peek().column)
                params.append(Param(name, ptype))
        self.consume("RPAREN")
        return params

    def parse_steps(self):
        steps = []
        while self.peek() and self.peek().type != "RBRACE":
            steps.append(self.parse_step())
        return steps

    def parse_step(self):
        token = self.peek()
        type_map = {
            "READ": self.parse_read, "HTTP": self.parse_http_read,
            "FILTER": self.parse_filter, "SELECT": self.parse_select,
            "JOIN": self.parse_join, "WRITE": self.parse_write,
            "GROUP": self.parse_group, "SORT": self.parse_sort,
            "DISTINCT": self.parse_distinct, "LIMIT": self.parse_limit,
            "MUTATE": self.parse_mutate, "UNION": self.parse_union,
            "RENAME": self.parse_rename, "PRINT": self.parse_print,
            "IF": self.parse_if, "LET": self.parse_let,
            "FOR": self.parse_for, "CASE": self.parse_case,
            "CAST": self.parse_cast, "SAMPLE": self.parse_sample,
            "STATS": self.parse_stats,
        }
        if token.type in type_map:
            return type_map[token.type]()
        raise ParserError(f"Unknown command: '{token.value}'", token.line, token.column,
                         hint="Valid commands: read, filter, select, sort, mutate, write, etc.")

    def parse_read(self):
        line = self.peek().line
        self.consume("READ")
        source = self.consume("STRING_LIT").value.strip('"')
        options = {}

        # Auto-detect format from extension
        if source.endswith(".json"):
            format_type = "json"
        elif source.endswith(".csv"):
            format_type = "csv"
        elif source.endswith(".parquet"):
            format_type = "parquet"
        else:
            format_type = "csv"

        alias = None

        # Check for "as" - could be format or alias
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            next_token = self.peek()
            if next_token and next_token.value in ("csv", "json", "parquet", "table"):
                format_type = self.consume().value
                if self.peek() and self.peek().type == "AS":
                    self.consume("AS")
                    alias = self.consume("IDENTIFIER").value
            else:
                alias = self.consume("IDENTIFIER").value

        return ReadStep(source, format_type, options, alias, line)

    def parse_http_read(self):
        line = self.peek().line
        self.consume("HTTP")
        self.consume("READ")
        url = self.consume("STRING_LIT").value.strip('"')
        format_type = "json"
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            format_type = self.consume().value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return HttpReadStep(url, format_type, alias, line)

    def parse_filter(self):
        line = self.peek().line
        self.consume("FILTER")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("WHERE")
        condition = self.parse_expression()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return FilterStep(input_ref, condition, alias, line)

    def parse_select(self):
        line = self.peek().line
        self.consume("SELECT")
        columns = self.parse_name_list()
        self.consume("FROM")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return SelectStep(input_ref, columns, alias, line)

    def parse_join(self):
        line = self.peek().line
        join_type = "inner"
        if self.peek().type in ("INNER", "LEFT", "RIGHT"):
            join_type = self.consume().value
        self.consume("JOIN")
        left_ref = self.consume("IDENTIFIER").value
        self.consume("WITH")
        right_ref = self.consume("IDENTIFIER").value
        self.consume("ON")
        on_column = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return JoinStep(left_ref, right_ref, on_column, join_type, alias, line)

    def parse_write(self):
        line = self.peek().line
        self.consume("WRITE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("INTO")
        target = self.consume("STRING_LIT").value.strip('"')

        # Auto-detect format from extension
        if target.endswith(".json"):
            format_type = "json"
        elif target.endswith(".csv"):
            format_type = "csv"
        else:
            format_type = "csv"

        # Check for explicit format
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            next_token = self.peek()
            if next_token and next_token.value in ("csv", "json", "parquet"):
                format_type = self.consume().value

        return WriteStep(input_ref, target, format_type, None, line)

    def parse_group(self):
        line = self.peek().line
        self.consume("GROUP")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("BY")
        key_column = self.consume("IDENTIFIER").value
        aggregations = self.parse_aggregations()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return GroupStep(input_ref, key_column, aggregations, alias, line)

    def parse_aggregations(self):
        aggs = []
        self.consume("LBRACKET")
        while self.peek().type != "RBRACKET":
            func = self.consume().value
            self.consume("LPAREN")
            column = self.consume("IDENTIFIER").value
            self.consume("RPAREN")
            self.consume("AS")
            output_name = self.consume("IDENTIFIER").value
            aggs.append(Aggregation(func, column, output_name))
            if self.peek().type == "COMMA":
                self.consume("COMMA")
        self.consume("RBRACKET")
        return aggs

    def parse_name_list(self):
        names = []
        if self.is_keyword_or_identifier(self.peek()):
            names.append(self.consume().value)
        else:
            raise ParserError(f"Expected column name, got {self.peek().type}", self.peek().line, self.peek().column)
        while self.peek().type == "COMMA":
            self.consume("COMMA")
            if self.is_keyword_or_identifier(self.peek()):
                names.append(self.consume().value)
            else:
                raise ParserError(f"Expected column name after comma", self.peek().line, self.peek().column)
        return names

    def parse_sort(self):
        line = self.peek().line
        self.consume("SORT")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("BY")
        column = self.peek().value
        self.consume()
        direction = "asc"
        if self.peek() and self.peek().type in ("ASC", "DESC"):
            direction = self.consume().value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return SortStep(input_ref, column, direction, alias, line)

    def parse_distinct(self):
        line = self.peek().line
        self.consume("DISTINCT")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return DistinctStep(input_ref, alias, line)

    def parse_limit(self):
        line = self.peek().line
        self.consume("LIMIT")
        input_ref = self.consume("IDENTIFIER").value
        count = int(self.consume("NUMBER_LIT").value)
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return LimitStep(input_ref, count, alias, line)

    def parse_mutate(self):
        line = self.peek().line
        self.consume("MUTATE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("ADD")
        new_column = self.peek().value
        self.consume()
        self.consume("ASSIGN")
        expression = self.parse_arithmetic()
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return MutateStep(input_ref, new_column, expression, alias, line)

    def parse_union(self):
        line = self.peek().line
        self.consume("UNION")
        left_ref = self.consume("IDENTIFIER").value
        self.consume("WITH")
        right_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return UnionStep(left_ref, right_ref, alias, line)

    def parse_rename(self):
        line = self.peek().line
        self.consume("RENAME")
        input_ref = self.consume("IDENTIFIER").value
        renames = {}
        old_name = self.peek().value
        self.consume()
        self.consume("TO")
        new_name = self.peek().value
        self.consume()
        renames[old_name] = new_name
        while self.peek().type == "COMMA":
            self.consume("COMMA")
            old_name = self.peek().value
            self.consume()
            self.consume("TO")
            new_name = self.peek().value
            self.consume()
            renames[old_name] = new_name
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return RenameStep(input_ref, renames, alias, line)

    def parse_print(self):
        line = self.peek().line
        self.consume("PRINT")
        input_ref = self.consume("IDENTIFIER").value
        return PrintStep(input_ref, line)

    def parse_if(self):
        line = self.peek().line
        self.consume("IF")
        condition = self.parse_expression()
        self.consume("LBRACE")
        if_body = self.parse_steps()
        self.consume("RBRACE")
        else_body = []
        if self.peek() and self.peek().type == "ELSE":
            self.consume("ELSE")
            self.consume("LBRACE")
            else_body = self.parse_steps()
            self.consume("RBRACE")
        return IfStep(condition, if_body, else_body, None, line)

    def parse_import(self):
        line = self.peek().line
        self.consume("IMPORT")
        filepath = self.consume("STRING_LIT").value.strip('"')
        return ImportStep(filepath, line)

    def parse_let(self):
        line = self.peek().line
        self.consume("LET")
        var_name = self.consume("IDENTIFIER").value
        self.consume("ASSIGN")
        value = self.parse_expression()
        return LetStep(var_name, value, None, line)

    def parse_for(self):
        line = self.peek().line
        self.consume("FOR")
        row_var = self.consume("IDENTIFIER").value
        self.consume("IN")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("LBRACE")
        body = self.parse_steps()
        self.consume("RBRACE")
        return ForStep(row_var, input_ref, body, None, line)

    def parse_case(self):
        line = self.peek().line
        self.consume("CASE")
        input_ref = self.consume("IDENTIFIER").value
        self.consume("WHEN")
        column = self.consume("IDENTIFIER").value
        self.consume("LBRACE")
        cases = []
        default_body = None
        while self.peek() and self.peek().type != "RBRACE":
            if self.peek().type == "WHEN":
                self.consume("WHEN")
                value = self.parse_primary()
                self.consume("LBRACE")
                body = self.parse_steps()
                self.consume("RBRACE")
                cases.append(CaseClause(value, body))
            elif self.peek().type == "ELSE":
                self.consume("ELSE")
                self.consume("LBRACE")
                default_body = self.parse_steps()
                self.consume("RBRACE")
            else:
                raise ParserError(f"Expected WHEN or ELSE, got {self.peek().type}", self.peek().line, self.peek().column)
        self.consume("RBRACE")
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return CaseStep(input_ref, column, cases, default_body, alias, line)

    def parse_cast(self):
        line = self.peek().line
        self.consume("CAST")
        input_ref = self.consume("IDENTIFIER").value
        column = self.consume("IDENTIFIER").value
        self.consume("AS")
        if self.is_type_token(self.peek()) or self.peek().type == "IDENTIFIER":
            new_type = self.consume().value
        else:
            raise ParserError(f"Expected type, got {self.peek().type}", self.peek().line, self.peek().column,
                            hint="Valid types: int, string, float, bool, date")
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return CastStep(input_ref, column, new_type, alias, line)

    def parse_sample(self):
        line = self.peek().line
        self.consume("SAMPLE")
        input_ref = self.consume("IDENTIFIER").value
        percent = float(self.consume("NUMBER_LIT").value)
        if self.peek().type == "PERCENT":
            self.consume("PERCENT")
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return SampleStep(input_ref, percent, alias, line)

    def parse_stats(self):
        line = self.peek().line
        self.consume("STATS")
        input_ref = self.consume("IDENTIFIER").value
        alias = None
        if self.peek() and self.peek().type == "AS":
            self.consume("AS")
            alias = self.consume("IDENTIFIER").value
        return StatsStep(input_ref, alias, line)

    # ============ EXPRESSIONS ============

    def parse_expression(self):
        if self.peek().type == "IDENTIFIER":
            left = self.parse_arithmetic()
            if self.peek() and self.peek().type == "IS":
                self.consume("IS")
                if self.peek().type == "NOT":
                    self.consume("NOT")
                    self.consume("NULL")
                    return BinaryOp(left, "is_not", NullLiteral())
                else:
                    self.consume("NULL")
                    return BinaryOp(left, "is", NullLiteral())
            if self.peek() and self.peek().type in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE", "AND", "OR",
                "CONTAINS", "MATCHES", "STARTS_WITH", "ENDS_WITH"):
                op = self.consume().value
                right = self.parse_expression()
                return BinaryOp(left, op, right)
            return left

        left = self.parse_arithmetic()
        if self.peek() and self.peek().type in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE", "AND", "OR",
            "CONTAINS", "MATCHES", "STARTS_WITH", "ENDS_WITH"):
            op = self.consume().value
            right = self.parse_expression()
            return BinaryOp(left, op, right)
        return left

    def parse_arithmetic(self):
        left = self.parse_primary()
        while self.peek() and self.peek().type in ("PLUS", "MINUS", "STAR", "SLASH"):
            op = self.consume().value
            right = self.parse_primary()
            left = ArithOp(left, op, right)
        return left

    def parse_primary(self):
        token = self.peek()
        if token.type == "STRING_LIT":
            self.consume()
            return StringLiteral(token.value.strip('"'))
        elif token.type == "NUMBER_LIT":
            self.consume()
            return NumberLiteral(float(token.value) if "." in token.value else int(token.value))
        elif token.type == "DATE_LIT":
            self.consume()
            d_str = token.value.strip('#')
            try:
                d = date.fromisoformat(d_str)
                return DateLiteral(d)
            except ValueError:
                raise ParserError(f"Invalid date: '{d_str}'", token.line, token.column,
                                hint="Use format: #YYYY-MM-DD#")
        elif token.type == "TRUE":
            self.consume()
            return BooleanLiteral(True)
        elif token.type == "FALSE":
            self.consume()
            return BooleanLiteral(False)
        elif token.type == "NULL":
            self.consume()
            return NullLiteral()
        elif token.type in ("CONCAT", "UPPER", "LOWER", "LENGTH", "TRIM",
                           "ABS", "ROUND", "CEIL", "FLOOR", "SQRT",
                           "YEAR", "MONTH", "DAY", "NOW", "TODAY", "POW"):
            func = self.consume().value
            self.consume("LPAREN")
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expression())
                while self.peek().type == "COMMA":
                    self.consume("COMMA")
                    args.append(self.parse_expression())
            self.consume("RPAREN")
            return FuncCall(func, args, token.line)
        elif token.type == "IDENTIFIER":
            self.consume()
            if self.peek() and self.peek().type == "DOT":
                self.consume("DOT")
                col = self.consume("IDENTIFIER").value
                return ColumnRef(token.value, col)
            if self.peek() and self.peek().type == "LPAREN":
                self.consume("LPAREN")
                args = []
                if self.peek().type != "RPAREN":
                    args.append(self.parse_expression())
                    while self.peek().type == "COMMA":
                        self.consume("COMMA")
                        args.append(self.parse_expression())
                self.consume("RPAREN")
                return FuncCall(token.value, args, token.line)
            return Identifier(token.value)
        elif token.type == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr
        else:
            raise ParserError(f"Unexpected token: {token.type} ('{token.value}')",
                            token.line, token.column,
                            hint="Expected a value, column name, or expression")