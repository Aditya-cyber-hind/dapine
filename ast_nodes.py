from datetime import date, datetime

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class Pipeline(ASTNode):
    def __init__(self, name, params, steps, line):
        self.name = name
        self.params = params
        self.steps = steps
        self.line = line

class Param(ASTNode):
    def __init__(self, name, ptype):
        self.name = name
        self.ptype = ptype

class Step(ASTNode):
    def __init__(self, operation, args, alias, line):
        self.operation = operation
        self.args = args
        self.alias = alias
        self.line = line

class ReadStep(Step):
    def __init__(self, source, format_type, options, alias, line):
        super().__init__("read", [source, format_type], alias, line)
        self.source = source
        self.format_type = format_type
        self.options = options or {}

class FilterStep(Step):
    def __init__(self, input_ref, condition, alias, line):
        super().__init__("filter", [input_ref, condition], alias, line)
        self.input_ref = input_ref
        self.condition = condition

class SelectStep(Step):
    def __init__(self, input_ref, columns, alias, line):
        super().__init__("select", [input_ref, columns], alias, line)
        self.input_ref = input_ref
        self.columns = columns

class JoinStep(Step):
    def __init__(self, left_ref, right_ref, on_column, join_type, alias, line):
        super().__init__("join", [left_ref, right_ref, on_column, join_type], alias, line)
        self.left_ref = left_ref
        self.right_ref = right_ref
        self.on_column = on_column
        self.join_type = join_type

class WriteStep(Step):
    def __init__(self, input_ref, target, format_type, alias, line):
        super().__init__("write", [input_ref, target, format_type], alias, line)
        self.input_ref = input_ref
        self.target = target
        self.format_type = format_type

class GroupStep(Step):
    def __init__(self, input_ref, key_column, aggregations, alias, line):
        super().__init__("group", [input_ref, key_column, aggregations], alias, line)
        self.input_ref = input_ref
        self.key_column = key_column
        self.aggregations = aggregations

class SortStep(Step):
    def __init__(self, input_ref, column, direction, alias, line):
        super().__init__("sort", [input_ref, column, direction], alias, line)
        self.input_ref = input_ref
        self.column = column
        self.direction = direction

class DistinctStep(Step):
    def __init__(self, input_ref, alias, line):
        super().__init__("distinct", [input_ref], alias, line)
        self.input_ref = input_ref

class LimitStep(Step):
    def __init__(self, input_ref, count, alias, line):
        super().__init__("limit", [input_ref, count], alias, line)
        self.input_ref = input_ref
        self.count = count

class MutateStep(Step):
    def __init__(self, input_ref, new_column, expression, alias, line):
        super().__init__("mutate", [input_ref, new_column, expression], alias, line)
        self.input_ref = input_ref
        self.new_column = new_column
        self.expression = expression

class UnionStep(Step):
    def __init__(self, left_ref, right_ref, alias, line):
        super().__init__("union", [left_ref, right_ref], alias, line)
        self.left_ref = left_ref
        self.right_ref = right_ref

class RenameStep(Step):
    def __init__(self, input_ref, renames, alias, line):
        super().__init__("rename", [input_ref, renames], alias, line)
        self.input_ref = input_ref
        self.renames = renames

class PrintStep(Step):
    def __init__(self, input_ref, line):
        super().__init__("print", [input_ref], None, line)
        self.input_ref = input_ref

class IfStep(Step):
    def __init__(self, condition, if_body, else_body, alias, line):
        super().__init__("if", [condition, if_body, else_body], alias, line)
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body

class HttpReadStep(Step):
    def __init__(self, url, format_type, alias, line):
        super().__init__("http_read", [url, format_type], alias, line)
        self.url = url
        self.format_type = format_type

class ImportStep(Step):
    def __init__(self, filepath, line):
        super().__init__("import", [filepath], None, line)
        self.filepath = filepath

class LetStep(Step):
    def __init__(self, var_name, value, alias, line):
        super().__init__("let", [var_name, value], alias, line)
        self.var_name = var_name
        self.value = value

class ForStep(Step):
    def __init__(self, row_var, input_ref, body, alias, line):
        super().__init__("for", [row_var, input_ref, body], alias, line)
        self.row_var = row_var
        self.input_ref = input_ref
        self.body = body

class CaseStep(Step):
    def __init__(self, input_ref, column, cases, default_alias, alias, line):
        super().__init__("case", [input_ref, column, cases], alias, line)
        self.input_ref = input_ref
        self.column = column
        self.cases = cases
        self.default_alias = default_alias

class CaseClause(ASTNode):
    def __init__(self, value, body):
        self.value = value
        self.body = body

class CastStep(Step):
    def __init__(self, input_ref, column, new_type, alias, line):
        super().__init__("cast", [input_ref, column, new_type], alias, line)
        self.input_ref = input_ref
        self.column = column
        self.new_type = new_type

class SampleStep(Step):
    def __init__(self, input_ref, percent, alias, line):
        super().__init__("sample", [input_ref, percent], alias, line)
        self.input_ref = input_ref
        self.percent = percent

class StatsStep(Step):
    def __init__(self, input_ref, alias, line):
        super().__init__("stats", [input_ref], alias, line)
        self.input_ref = input_ref

class Aggregation(ASTNode):
    def __init__(self, func, column, output_name):
        self.func = func
        self.column = column
        self.output_name = output_name

class BinaryOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name

class StringLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class NumberLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class BooleanLiteral(ASTNode):
    def __init__(self, value):
        self.value = value

class DateLiteral(ASTNode):
    def __init__(self, value):
        self.value = value  # date object

class NullLiteral(ASTNode):
    pass

class ColumnRef(ASTNode):
    def __init__(self, table, column):
        self.table = table
        self.column = column

class ArithOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class FuncCall(ASTNode):
    def __init__(self, name, args, line):
        self.name = name
        self.args = args
        self.line = line

class FuncDef(ASTNode):
    def __init__(self, name, params, body_expr, line):
        self.name = name
        self.params = params
        self.body_expr = body_expr
        self.line = line