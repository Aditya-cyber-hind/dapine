from errors import LexerError
import re

KEYWORDS = {
    "pipeline": "PIPELINE", "filter": "FILTER", "select": "SELECT",
    "where": "WHERE", "join": "JOIN", "inner": "INNER",
    "left": "LEFT", "right": "RIGHT", "write": "WRITE",
    "group": "GROUP", "read": "READ", "from": "FROM",
    "into": "INTO", "with": "WITH", "on": "ON", "by": "BY",
    "as": "AS", "and": "AND", "or": "OR", "not": "NOT",
    "sum": "SUM", "count": "COUNT", "avg": "AVG",
    "min": "MIN", "max": "MAX", "table": "TABLE",
    "int": "INT", "string": "STRING", "float": "FLOAT",
    "bool": "BOOL", "date": "DATE",
    "sort": "SORT", "asc": "ASC", "desc": "DESC",
    "distinct": "DISTINCT", "limit": "LIMIT",
    "mutate": "MUTATE", "add": "ADD", "union": "UNION",
    "rename": "RENAME", "to": "TO", "print": "PRINT",
    "if": "IF", "else": "ELSE", "http": "HTTP",
    "import": "IMPORT", "let": "LET", "for": "FOR",
    "in": "IN", "func": "FUNC", "case": "CASE",
    "when": "WHEN", "cast": "CAST", "sample": "SAMPLE",
    "stats": "STATS", "true": "TRUE", "false": "FALSE",
    "null": "NULL", "is": "IS",
    "contains": "CONTAINS", "matches": "MATCHES",
    "starts_with": "STARTS_WITH", "ends_with": "ENDS_WITH",
    "concat": "CONCAT", "upper": "UPPER", "lower": "LOWER",
    "length": "LENGTH", "trim": "TRIM",
    "abs": "ABS", "round": "ROUND", "ceil": "CEIL",
    "floor": "FLOOR", "sqrt": "SQRT", "pow": "POW",
    "now": "NOW", "today": "TODAY",
    "year": "YEAR", "month": "MONTH", "day": "DAY",
    "chart": "CHART", "bar": "BAR", "line": "LINE", "pie": "PIE",
    "scatter": "SCATTER", "radar": "RADAR",
    "date_add": "DATE_ADD", "date_diff": "DATE_DIFF",
    "date_format": "DATE_FORMAT", "day_name": "DAY_NAME",
    "month_name": "MONTH_NAME",
    "chart": "CHART", "bar": "BAR", "line": "LINE", "pie": "PIE",
    "scatter": "SCATTER", "radar": "RADAR",
    "date_add": "DATE_ADD", "date_diff": "DATE_DIFF",
    "date_format": "DATE_FORMAT", "day_name": "DAY_NAME",
    "month_name": "MONTH_NAME",
    "train": "TRAIN", "predict": "PREDICT", "using": "USING",
    "model": "MODEL", "linear_regression": "LINEAR_REGRESSION",
    "random_forest": "RANDOM_FOREST", "decision_tree": "DECISION_TREE",
    "logistic_regression": "LOGISTIC_REGRESSION",
    "random_forest_classifier": "RANDOM_FOREST_CLASSIFIER",
    "decision_tree_classifier": "DECISION_TREE_CLASSIFIER",
    "db_read": "DB_READ", "db_write": "DB_WRITE",
    "excel": "EXCEL", "xlsx": "XLSX", "sheet": "SHEET",
    "report": "REPORT",
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
                    if self.source[self.pos] == "\n":
                        self.line += 1; self.column = 1
                    else:
                        self.column += 1
                    self.pos += 1
                self.pos += 2; self.column += 2
                continue
            
            if ch == "\n":
                self.line += 1; self.column = 1; self.pos += 1; continue
            
            if ch == '"':
                start = self.pos; self.pos += 1; self.column += 1
                while self.pos < len(self.source) and self.source[self.pos] != '"':
                    if self.source[self.pos] == '\n':
                        self.line += 1; self.column = 1
                    else:
                        self.column += 1
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
                        raise LexerError("Unterminated date literal", self.line, self.column)
                    self.pos += 1; self.column += 1
                if self.pos >= len(self.source):
                    raise LexerError("Unterminated date literal", self.line, self.column)
                self.pos += 1; self.column += 1
                self.tokens.append(Token("DATE_LIT", self.source[start:self.pos], self.line, self.column - (self.pos - start)))
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