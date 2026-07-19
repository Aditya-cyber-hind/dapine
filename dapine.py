import sys
import os
import glob
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import DapineError

def print_usage():
    print("""
╔══════════════════════════════════════════╗
║        🚀 DAPINE v2.0 🚀                ║
║    Data Pipeline Language                ║
╚══════════════════════════════════════════╝

Usage:
  python dapine.py                        Run main.dap (default)
  python dapine.py file.dap               Run a specific file
  python dapine.py list                   List all .dap files
  python dapine.py help                   Show this help
  python repl.py                          Interactive REPL mode

Examples:
  python dapine.py                        Runs main.dap
  python dapine.py my_pipeline.dap        Runs my_pipeline.dap
  python dapine.py examples/test_all.dap  Runs the test suite
""")

def list_dap_files():
    """List all .dap files in current directory and examples folder."""
    files = glob.glob("*.dap") + glob.glob("examples/*.dap")
    if files:
        print("\n📁 Available .dap files:")
        for f in sorted(files):
            size = os.path.getsize(f)
            print(f"  📄 {f} ({size} bytes)")
    else:
        print("\n📁 No .dap files found.")
        print("   Create a file ending in .dap to get started!")

def run_file(filename):
    """Execute a .dap file."""
    if not os.path.exists(filename):
        print(f"\n❌ File not found: '{filename}'")
        print(f"   Hint: Make sure the file exists. Use 'python dapine.py list' to see available files.")
        
        # Suggest similar files
        all_files = glob.glob("*.dap") + glob.glob("examples/*.dap")
        if all_files:
            from difflib import get_close_matches
            matches = get_close_matches(filename, all_files, n=3)
            if matches:
                print(f"   Did you mean?")
                for m in matches:
                    print(f"     • {m}")
        sys.exit(1)
    
    try:
        with open(filename, "r") as f:
            source = f.read()
        
        if not source.strip():
            print(f"\n❌ File '{filename}' is empty!")
            sys.exit(1)
        
        print(f"\n📄 Running: {filename}")
        print(f"   Size: {len(source)} characters, {len(source.splitlines())} lines")
        
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
        
        print(f"\n✅ {filename} executed successfully!")
        
    except DapineError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        # No arguments - try main.dap
        if os.path.exists("main.dap"):
            run_file("main.dap")
        else:
            print_usage()
            list_dap_files()
            sys.exit(0)
    else:
        command = sys.argv[1].lower()
        
        if command == "help" or command == "--help" or command == "-h":
            print_usage()
        elif command == "list" or command == "ls":
            list_dap_files()
        else:
            # Treat as filename
            run_file(sys.argv[1])

if __name__ == "__main__":
    main()