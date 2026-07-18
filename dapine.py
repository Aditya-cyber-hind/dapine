import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import DapineError

def main():
    if len(sys.argv) < 2:
        print("Usage: python dapine.py <file.dap>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, "r") as f:
            source = f.read()

        # Lex
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Parse
        parser = Parser(tokens)
        ast = parser.parse()

        # Pass functions to interpreter
        interpreter = Interpreter()
        interpreter.runtime.functions = parser.functions

        # Execute
        interpreter.execute(ast)

        print("\n✓ Dapine finished successfully.")

    except DapineError as e:
        print(f"\n{e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n  Error: File '{filename}' not found.")
        print(f"  Hint: Make sure the file exists and the path is correct.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()