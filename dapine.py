import sys
import os
import glob
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import DapineError

def print_usage():
    print("""
DAPINE v2.7 - Data Pipeline Language

Usage:
  python dapine.py                  Run main.dap (default)
  python dapine.py file.dap         Run a specific file
  python dapine.py list             List all .dap files
  python dapine.py help             Show this help
  python dapine.py install pkg      Install a package
  python dapine.py uninstall pkg    Uninstall a package
  python dapine.py search query     Search packages
  python dapine.py pkg-list         List installed packages
  python repl.py                    Interactive REPL mode
""")

def list_dap_files():
    files = glob.glob("*.dap") + glob.glob("examples/*.dap")
    if files:
        print("\nAvailable .dap files:")
        for f in sorted(files):
            size = os.path.getsize(f)
            print(f"  {f} ({size} bytes)")
    else:
        print("\nNo .dap files found.")

def run_file(filename):
    if not os.path.exists(filename):
        print(f"\nFile not found: '{filename}'")
        list_dap_files()
        sys.exit(1)
    try:
        with open(filename, "r") as f:
            source = f.read()
        if not source.strip():
            print(f"\nFile '{filename}' is empty!")
            sys.exit(1)
        print(f"\nRunning: {filename}")
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        interpreter.runtime.functions = parser.functions
        interpreter.execute(ast)
        print(f"\n{filename} executed successfully!")
    except DapineError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        if os.path.exists("main.dap"):
            run_file("main.dap")
        else:
            print_usage()
            list_dap_files()
        return

    command = sys.argv[1].lower()

    if command in ("help", "--help", "-h"):
        print_usage()
    elif command in ("list", "ls"):
        list_dap_files()
    elif command == "install":
        if len(sys.argv) > 2:
            from dap_pm import PackageManager
            PackageManager().install(sys.argv[2])
        else:
            print("Usage: python dapine.py install <package_name>")
    elif command == "uninstall":
        if len(sys.argv) > 2:
            from dap_pm import PackageManager
            PackageManager().uninstall(sys.argv[2])
        else:
            print("Usage: python dapine.py uninstall <package_name>")
    elif command == "search":
        from dap_pm import PackageManager
        PackageManager().search(sys.argv[2] if len(sys.argv) > 2 else "")
    elif command == "pkg-list":
        from dap_pm import PackageManager
        PackageManager().list_installed()
    else:
        run_file(sys.argv[1])

if __name__ == "__main__":
    main()