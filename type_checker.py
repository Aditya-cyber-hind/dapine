from errors import DapineTypeError
from ast_nodes import *

class TypeChecker:
    def __init__(self):
        self.schemas = {}

    def check(self, program):
        for pipeline in program.statements:
            self.check_pipeline(pipeline)

    def check_pipeline(self, pipeline):
        current_schema = None
        for step in pipeline.steps:
            if isinstance(step, ReadStep):
                current_schema = self.infer_read_schema(step)
            elif isinstance(step, FilterStep):
                if step.input_ref not in self.schemas:
                    raise DapineTypeError(f"Unknown reference: {step.input_ref}", step.line)
                current_schema = self.schemas[step.input_ref]
            elif isinstance(step, SelectStep):
                if step.input_ref not in self.schemas:
                    raise DapineTypeError(f"Unknown reference: {step.input_ref}", step.line)
                current_schema = [c for c in self.schemas[step.input_ref] if c in step.columns]
            elif isinstance(step, JoinStep):
                if step.left_ref not in self.schemas:
                    raise DapineTypeError(f"Unknown reference: {step.left_ref}", step.line)
                if step.right_ref not in self.schemas:
                    raise DapineTypeError(f"Unknown reference: {step.right_ref}", step.line)
                current_schema = self.schemas[step.left_ref] + self.schemas[step.right_ref]
            elif isinstance(step, GroupStep):
                if step.input_ref not in self.schemas:
                    raise DapineTypeError(f"Unknown reference: {step.input_ref}", step.line)
                agg_cols = [a.output_name for a in step.aggregations]
                current_schema = [step.key_column] + agg_cols
            if step.alias:
                self.schemas[step.alias] = current_schema or []

    def infer_read_schema(self, step):
        if step.format_type == "csv":
            return ["_inferred_from_file"]
        return ["_unknown"]