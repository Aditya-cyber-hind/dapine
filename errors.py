class DapineError(Exception):
    def __init__(self, message, line=None, column=None, hint=None):
        self.line = line
        self.column = column
        self.hint = hint
        loc = ""
        if line is not None:
            loc = f" at line {line}"
            if column is not None:
                loc += f", column {column}"
        msg = f"\n  Error{loc}: {message}"
        if hint:
            msg += f"\n  Hint: {hint}"
        super().__init__(msg)

class LexerError(DapineError):
    pass

class ParserError(DapineError):
    pass

class DapineTypeError(DapineError):
    pass

class RuntimeError(DapineError):
    pass

class ColumnNotFoundError(RuntimeError):
    def __init__(self, column, available, line=None):
        hint = None
        if available:
            from difflib import get_close_matches
            matches = get_close_matches(column, available, n=2)
            if matches:
                hint = f"Did you mean '{matches[0]}'?"
                if len(matches) > 1:
                    hint += f" or '{matches[1]}'?"
        super().__init__(f"Column '{column}' not found", line, hint=hint)

class DataFrameNotFoundError(RuntimeError):
    def __init__(self, name, available, line=None):
        hint = None
        if available:
            from difflib import get_close_matches
            matches = get_close_matches(name, available, n=2)
            if matches:
                hint = f"Did you mean '{matches[0]}'?"
        super().__init__(f"DataFrame '{name}' not found", line, hint=hint)

class FileNotFoundError(DapineError):
    def __init__(self, filepath, line=None):
        super().__init__(f"File not found: '{filepath}'", line, 
                        hint="Make sure the file exists and the path is correct")