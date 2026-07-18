import sys
import os
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter
from errors import DapineError
from runtime import Runtime

# Colors for terminal (Windows 10+ supports ANSI)
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
  ╔══════════════════════════════════════╗
  ║       🚀 DAPINE REPL v2.0 🚀        ║
  ║    Your Data Pipeline Language       ║
  ╚══════════════════════════════════════╝
{Colors.RESET}
  Type Dapine commands and see results instantly!
  Commands:
    {Colors.GREEN}/help{Colors.RESET}     - Show this message
    {Colors.GREEN}/tables{Colors.RESET}   - List all tables
    {Colors.GREEN}/vars{Colors.RESET}     - List all variables  
    {Colors.GREEN}/funcs{Colors.RESET}    - List all functions
    {Colors.GREEN}/lineage{Colors.RESET}  - Show data lineage
    {Colors.GREEN}/clear{Colors.RESET}    - Clear all data
    {Colors.GREEN}/exit{Colors.RESET}     - Exit REPL
    {Colors.GREEN}/run file{Colors.RESET} - Run a .dap file
""")

class Repl:
    def __init__(self):
        self.runtime = Runtime()
        self.step_count = 0
        
    def start(self):
        print_banner()
        
        while True:
            try:
                # Get input
                line = input(f"{Colors.BOLD}dap> {Colors.RESET}").strip()
                
                if not line:
                    continue
                
                # Handle special commands
                if line.startswith("/"):
                    self.handle_command(line)
                    continue
                
                # Execute Dapine code
                self.execute_line(line)
                
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Use /exit to quit{Colors.RESET}")
            except EOFError:
                break
        
        print(f"\n{Colors.CYAN}Goodbye! 👋{Colors.RESET}")
    
    def handle_command(self, cmd):
        parts = cmd.split()
        command = parts[0].lower()
        
        if command == "/exit" or command == "/quit":
            print(f"{Colors.CYAN}Goodbye! 👋{Colors.RESET}")
            sys.exit(0)
        
        elif command == "/help":
            print_banner()
        
        elif command == "/tables":
            if self.runtime.dataframes:
                print(f"\n{Colors.GREEN}📊 Tables ({len(self.runtime.dataframes)}):{Colors.RESET}")
                for name, df in self.runtime.dataframes.items():
                    print(f"  {Colors.BOLD}{name}{Colors.RESET}: {len(df.rows)} rows × {len(df.schema)} cols")
                    print(f"    Columns: {', '.join(df.schema)}")
            else:
                print(f"{Colors.YELLOW}No tables yet. Read some data first!{Colors.RESET}")
        
        elif command == "/vars":
            if self.runtime.variables:
                print(f"\n{Colors.GREEN}📦 Variables ({len(self.runtime.variables)}):{Colors.RESET}")
                for name, val in self.runtime.variables.items():
                    print(f"  {Colors.BOLD}{name}{Colors.RESET} = {val}")
            else:
                print(f"{Colors.YELLOW}No variables defined yet.{Colors.RESET}")
        
        elif command == "/funcs":
            if self.runtime.functions:
                print(f"\n{Colors.GREEN}🔧 Functions ({len(self.runtime.functions)}):{Colors.RESET}")
                for name, func in self.runtime.functions.items():
                    params = ", ".join(func.params)
                    print(f"  {Colors.BOLD}{name}{Colors.RESET}({params})")
            else:
                print(f"{Colors.YELLOW}No functions defined yet.{Colors.RESET}")
        
        elif command == "/lineage":
            if self.runtime.lineage_log:
                print(f"\n{Colors.GREEN}📋 Lineage ({len(self.runtime.lineage_log)} steps):{Colors.RESET}")
                for entry in self.runtime.lineage_log:
                    print(f"  {entry}")
            else:
                print(f"{Colors.YELLOW}No lineage yet. Run some transformations!{Colors.RESET}")
        
        elif command == "/clear":
            self.runtime = Runtime()
            self.step_count = 0
            print(f"{Colors.GREEN}✅ All data cleared!{Colors.RESET}")
        
        elif command == "/run":
            if len(parts) > 1:
                filename = parts[1]
                self.run_file(filename)
            else:
                print(f"{Colors.RED}Usage: /run filename.dap{Colors.RESET}")
        
        else:
            print(f"{Colors.RED}Unknown command: {command}{Colors.RESET}")
    
    def run_file(self, filename):
        try:
            with open(filename, "r") as f:
                source = f.read()
            
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            # Merge parser's functions into runtime
            self.runtime.functions.update(parser.functions)
            
            interpreter = Interpreter()
            interpreter.runtime = self.runtime
            
            print(f"\n{Colors.CYAN}Running {filename}...{Colors.RESET}")
            interpreter.execute(ast)
            print(f"{Colors.GREEN}✅ File executed successfully!{Colors.RESET}")
            
        except FileNotFoundError:
            print(f"{Colors.RED}File not found: {filename}{Colors.RESET}")
        except DapineError as e:
            print(f"\n{Colors.RED}{e}{Colors.RESET}")
    
    def execute_line(self, line):
        try:
            source = line
            
            # Only auto-wrap if it's a step command (not func/import/pipeline)
            first_word = line.split()[0].lower() if line.split() else ""
            pipeline_keywords = ["pipeline", "func", "import"]
            
            if first_word not in pipeline_keywords:
                source = f"pipeline _repl() {{\n{line}\n}}"
            
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            
            self.runtime.functions.update(parser.functions)
            
            interpreter = Interpreter()
            interpreter.runtime = self.runtime
            
            interpreter.execute(ast)
            print(f"{Colors.GREEN}✅ Done!{Colors.RESET}")
            
        except DapineError as e:
            print(f"\n{Colors.RED}{e}{Colors.RESET}")
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    repl = Repl()
    repl.start()