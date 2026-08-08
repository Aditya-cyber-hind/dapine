from errors import LexerError

KEYWORDS = {
    # Pipeline
    "pipeline": "PIPELINE", "func": "FUNC", "import": "IMPORT",
    "let": "LET", "as": "AS", "in": "IN",
    
    # I/O
    "read": "READ", "write": "WRITE", "http": "HTTP",
    "excel": "EXCEL", "into": "INTO", "from": "FROM",
    
    # Transform
    "filter": "FILTER", "where": "WHERE", "select": "SELECT",
    "sort": "SORT", "by": "BY", "limit": "LIMIT",
    "mutate": "MUTATE", "add": "ADD", "rename": "RENAME",
    "cast": "CAST", "sample": "SAMPLE", "distinct": "DISTINCT",
    
    # Aggregate
    "group": "GROUP", "join": "JOIN", "union": "UNION",
    "with": "WITH", "on": "ON", "inner": "INNER",
    "left": "LEFT", "right": "RIGHT",
    
    # ML
    "train": "TRAIN", "predict": "PREDICT", "using": "USING",
    "model": "MODEL", "linear_regression": "LINEAR_REGRESSION",
    "random_forest": "RANDOM_FOREST", "decision_tree": "DECISION_TREE",
    
    # Output
    "print": "PRINT", "stats": "STATS", "chart": "CHART",
    "report": "REPORT", "alert": "ALERT",
    
    # Control Flow
    "if": "IF", "else": "ELSE", "for": "FOR",
    "case": "CASE", "when": "WHEN",
    
    # NEW: Error Handling
    "try": "TRY", "catch": "CATCH",
    
    # NEW: Pivot & Window
    "pivot": "PIVOT", "rows": "ROWS", "to": "TO",
    "columns": "COLUMNS", "rank": "RANK", "over": "OVER",
    "partition": "PARTITION", "order": "ORDER",
    
    # NEW: CTE
    "define": "DEFINE",
    
    # NEW: Export
    "export": "EXPORT", "sql": "SQL", "pdf": "PDF",
    "email": "EMAIL", "slack": "SLACK", "upload": "UPLOAD",
    "s3": "S3",
    
    # Types
    "table": "TABLE", "int": "INT", "string": "STRING",
    "float": "FLOAT", "bool": "BOOL", "date": "DATE",
    
    # Direction
    "asc": "ASC", "desc": "DESC",
    
    # Chart types
    "bar": "BAR", "pie": "PIE", "line": "LINE",
    "scatter": "SCATTER", "radar": "RADAR",
    
    # Boolean & Null
    "true": "TRUE", "false": "FALSE", "null": "NULL",
    "is": "IS", "not": "NOT", "and": "AND", "or": "OR",
    
    # Aggregation functions
    "count": "COUNT", "sum": "SUM", "avg": "AVG",
    "min": "MIN", "max": "MAX",
    
    # Built-in functions
    "upper": "UPPER", "lower": "LOWER", "length": "LENGTH",
    "trim": "TRIM", "concat": "CONCAT",
    "abs": "ABS", "round": "ROUND", "ceil": "CEIL",
    "floor": "FLOOR", "sqrt": "SQRT", "pow": "POW",
    "today": "TODAY", "now": "NOW",
    "year": "YEAR", "month": "MONTH", "day": "DAY",
    "date_add": "DATE_ADD", "date_diff": "DATE_DIFF",
    "date_format": "DATE_FORMAT", "day_name": "DAY_NAME",
    "month_name": "MONTH_NAME",
    
    # NEW: Regex
    "matches": "MATCHES", "contains": "CONTAINS",
    "starts_with": "STARTS_WITH", "ends_with": "ENDS_WITH",

    "schedule": "SCHEDULE", "seconds": "SECONDS",
    "minutes": "MINUTES", "hours": "HOURS",
    "daily": "DAILY",
    "serve": "SERVE",
    "translate": "TRANSLATE",
    "anomaly": "ANOMALY", "zscore": "ZSCORE",
}

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            
            if ch in " \t\r":
                self.pos += 1; self.column += 1; continue
            
            if self.source[self.pos:self.pos+2] == "//":
                while self.pos < len(self.source) and self.source[self.pos] != "\n":
                    self.pos += 1
                continue
            
            if self.source[self.pos:self.pos+2] == "/*":
                self.pos += 2; self.column += 2
                while self.pos < len(self.source) and self.source[self.pos:self.pos+2] != "*/":
                    if self.source[self.pos] == "\n": self.line += 1; self.column = 1
                    else: self.column += 1
                    self.pos += 1
                self.pos += 2; self.column += 2
                continue
            
            if ch == "\n":
                self.line += 1; self.column = 1; self.pos += 1; continue
            
            if ch == '"':
                start = self.pos; self.pos += 1; self.column += 1
                while self.pos < len(self.source) and self.source[self.pos] != '"':
                    if self.source[self.pos] == '\n': self.line += 1; self.column = 1
                    else: self.column += 1
                    self.pos += 1
                if self.pos >= len(self.source):
                    raise LexerError("Unterminated string", self.line, self.column)
                self.pos += 1; self.column += 1
                self.tokens.append(Token("STRING_LIT", self.source[start:self.pos], self.line, self.column - (self.pos - start)))
                continue
            
            # Date literal: #2024-01-15#
            if ch == '#':
                start = self.pos; self.pos += 1; self.column += 1
                while self.pos < len(self.source) and self.source[self.pos] != '#':
                    if self.source[self.pos] == '\n':
                        raise LexerError("Unterminated date", self.line, self.column)
                    self.pos += 1; self.column += 1
                if self.pos >= len(self.source):
                    raise LexerError("Unterminated date", self.line, self.column)
                self.pos += 1; self.column += 1
                self.tokens.append(Token("DATE_LIT", self.source[start:self.pos], self.line, self.column - (self.pos - start)))
                continue
            
            # NEW: Multi-line string """
            if self.source[self.pos:self.pos+3] == '"""':
                start = self.pos; self.pos += 3; self.column += 3
                while self.pos < len(self.source) and self.source[self.pos:self.pos+3] != '"""':
                    if self.source[self.pos] == '\n': self.line += 1; self.column = 1
                    else: self.column += 1
                    self.pos += 1
                self.pos += 3; self.column += 3
                self.tokens.append(Token("STRING_LIT", self.source[start:self.pos], self.line, self.column - (self.pos - start)))
                continue
            
            # NEW: Template string ${...}
            if self.source[self.pos:self.pos+2] == '${':
                start = self.pos; self.pos += 2; self.column += 2
                while self.pos < len(self.source) and self.source[self.pos] != '}':
                    if self.source[self.pos] == '\n': self.line += 1; self.column = 1
                    else: self.column += 1
                    self.pos += 1
                self.pos += 1; self.column += 1
                self.tokens.append(Token("TEMPLATE", self.source[start:self.pos], self.line, self.column - (self.pos - start)))
                continue
            
            if ch.isdigit():
                start = self.pos; start_col = self.column
                while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
                    self.pos += 1; self.column += 1
                self.tokens.append(Token("NUMBER_LIT", self.source[start:self.pos], self.line, start_col))
                continue
            
            if ch.isalpha() or ch == '_':
                start = self.pos; start_col = self.column
                while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
                    self.pos += 1; self.column += 1
                word = self.source[start:self.pos]
                if word in KEYWORDS:
                    self.tokens.append(Token(KEYWORDS[word], word, self.line, start_col))
                else:
                    self.tokens.append(Token("IDENTIFIER", word, self.line, start_col))
                continue
            
            # NEW: Lambda arrow =>
            if self.source[self.pos:self.pos+2] == "=>":
                self.tokens.append(Token("ARROW", "=>", self.line, self.column))
                self.pos += 2; self.column += 2; continue
            
            two_char = self.source[self.pos:self.pos+2]
            if two_char in ("->", "==", "!=", ">=", "<="):
                types = {"->": "ARROW", "==": "EQ", "!=": "NEQ", ">=": "GTE", "<=": "LTE"}
                self.tokens.append(Token(types[two_char], two_char, self.line, self.column))
                self.pos += 2; self.column += 2; continue
            
            single = {"{": "LBRACE", "}": "RBRACE", "(": "LPAREN", ")": "RPAREN",
                      "[": "LBRACKET", "]": "RBRACKET", ",": "COMMA", ":": "COLON",
                      ".": "DOT", "=": "ASSIGN", ">": "GT", "<": "LT",
                      "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT"}
            if ch in single:
                self.tokens.append(Token(single[ch], ch, self.line, self.column))
                self.pos += 1; self.column += 1; continue
            
            raise LexerError(f"Unexpected character: '{ch}'", self.line, self.column,
                           hint="Check for typos or unsupported symbols")
        
        self.tokens.append(Token("EOF", None, self.line, self.column))
        return self.tokens