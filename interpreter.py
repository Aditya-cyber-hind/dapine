from ast_nodes import *
from runtime import Runtime, DataFrame
from errors import RuntimeError, DapineError
import os

class Interpreter:
    def __init__(self):
        self.runtime = Runtime()

    def execute(self, program):
        results = []
        for statement in program.statements:
            if isinstance(statement, Pipeline):
                results.append(self.execute_pipeline(statement))
            elif isinstance(statement, ImportStep):
                self.execute_import(statement)
            elif isinstance(statement, FuncDef):
                self.runtime.functions[statement.name] = statement
        return results

    def execute_import(self, step):
        filepath = step.filepath
        if not os.path.exists(filepath):
            raise RuntimeError(f"Import file not found: '{filepath}'", step.line,
                             hint="Check the file path and make sure it exists")
        with open(filepath, "r") as f:
            source = f.read()
        from lexer import Lexer
        from parser import Parser
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        parser.functions = self.runtime.functions
        ast = parser.parse()
        self.runtime.functions.update(parser.functions)
        self.execute(ast)

    def execute_pipeline(self, pipeline):
        print(f"\n{'='*60}")
        print(f"  🚀 Running pipeline: {pipeline.name}")
        print(f"{'='*60}")
        result = None
        step_count = 0
        for step in pipeline.steps:
            step_count += 1
            try:
                result = self.execute_step(step)
                if result is not None:
                    if hasattr(result, 'rows'):
                        print(f"  ✅ Step {step_count}: {step.operation} → {len(result.rows)} rows")
                    else:
                        print(f"  ✅ Step {step_count}: {step.operation} = {result}")
                else:
                    print(f"  ✅ Step {step_count}: {step.operation}")
            except DapineError as e:
                print(f"  ❌ Step {step_count} failed: {step.operation}")
                raise
        print(f"\n{'='*60}")
        print(f"  ✅ Pipeline '{pipeline.name}' completed: {step_count} steps")
        print(f"  📋 Lineage: {len(self.runtime.lineage_log)} transformations tracked")
        print(f"{'='*60}")
        return result

    def execute_step(self, step):
        if isinstance(step, ReadStep):
            return self.runtime.execute_read(step)
        elif isinstance(step, HttpReadStep):
            return self.runtime.execute_http_read(step)
        elif isinstance(step, FilterStep):
            return self.runtime.execute_filter(step)
        elif isinstance(step, SelectStep):
            return self.runtime.execute_select(step)
        elif isinstance(step, JoinStep):
            return self.runtime.execute_join(step)
        elif isinstance(step, GroupStep):
            return self.runtime.execute_group(step)
        elif isinstance(step, WriteStep):
            self.runtime.execute_write(step)
        elif isinstance(step, SortStep):
            return self.runtime.execute_sort(step)
        elif isinstance(step, DistinctStep):
            return self.runtime.execute_distinct(step)
        elif isinstance(step, LimitStep):
            return self.runtime.execute_limit(step)
        elif isinstance(step, MutateStep):
            return self.runtime.execute_mutate(step)
        elif isinstance(step, UnionStep):
            return self.runtime.execute_union(step)
        elif isinstance(step, RenameStep):
            return self.runtime.execute_rename(step)
        elif isinstance(step, PrintStep):
            return self.runtime.execute_print(step)
        elif isinstance(step, LetStep):
            return self.runtime.execute_let(step)
        elif isinstance(step, ForStep):
            return self.runtime.execute_for(step)
        elif isinstance(step, CaseStep):
            return self.runtime.execute_case(step)
        elif isinstance(step, CastStep):
            return self.runtime.execute_cast(step)
        elif isinstance(step, SampleStep):
            return self.runtime.execute_sample(step)
        elif isinstance(step, StatsStep):
            return self.runtime.execute_stats(step)
        elif isinstance(step, IfStep):
            return self.runtime.execute_if(step)
        elif isinstance(step, ChartStep):
            return self.runtime.execute_chart(step)
        elif isinstance(step, TrainStep):
            return self.runtime.execute_train(step)
        elif isinstance(step, PredictStep):
            return self.runtime.execute_predict(step)
        else:
            raise RuntimeError(f"Unknown step: {step.operation}", step.line)
        return None