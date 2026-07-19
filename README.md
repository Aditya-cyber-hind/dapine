\# Dapine - Data Pipeline Language



A simple data pipeline language built in Python. Transform CSV/JSON data with an easy-to-read syntax. Now with Machine Learning, Charts, and REPL mode.



\## Features



\- Read CSV, JSON files (auto-detect format)

\- Filter with ==, !=, >, <, >=, <=, AND, OR, starts\_with, contains, ends\_with

\- Aggregate with group by (count, sum, avg, min, max)

\- Transform with mutate, rename, select, cast

\- Stats - min, max, mean, median, stdev

\- Strings - upper, lower, length, trim, concat

\- Math - abs, round, sqrt, ceil, floor, pow

\- Dates - today, year, month, day, date\_add, date\_diff, date\_format

\- Write CSV, JSON output

\- Lineage tracking - know where every value came from

\- REPL mode - interactive data exploration

\- Custom functions with func

\- Control flow - let, for, if/else, case/when

\- Charts - bar, pie, line, scatter, radar (opens in browser)

\- Machine Learning - train models, make predictions (linear regression, random forest, decision tree)



\## Quick Start



git clone https://github.com/Aditya-cyber-hind/dapine.git

cd dapine

pip install duckdb scikit-learn

python dapine.py examples/test\_all.dap

python repl.py



\## Example Pipeline



func double(x) = x \* 2



pipeline analyze\_users() {

&#x20;   read "data.csv" as raw

&#x20;   print raw

&#x20;   stats raw

&#x20;   filter raw where age >= 18 as adults

&#x20;   mutate adults add doubled\_age = double(age) as with\_double

&#x20;   group with\_double by city \[

&#x20;       count(name) as users,

&#x20;       avg(age) as avg\_age

&#x20;   ] as report

&#x20;   sort report by users desc as final

&#x20;   write final into "report.json"

&#x20;   chart final users by city as bar into "chart.html"

}



\## Machine Learning



pipeline predict\_prices() {

&#x20;   read "houses.csv" as data

&#x20;   stats data

&#x20;   train data predict price using linear\_regression as model

&#x20;   read "new\_houses.csv" as new\_data

&#x20;   predict new\_data using model as estimated\_price

&#x20;   print estimated\_price

&#x20;   write estimated\_price into "predictions.json"

}



\## REPL Mode



dap> read "data.csv" as raw

dap> print raw

dap> filter raw where age > 18 as adults

dap> stats adults

dap> /tables

dap> /lineage

dap> /exit



\## Syntax Reference



| Task | Syntax |

|------|--------|

| Read CSV | read "file.csv" as name |

| Read JSON | read "file.json" as name |

| Print | print name |

| Stats | stats name |

| Filter | filter name where col > 10 as result |

| Sort asc | sort name by col asc as result |

| Sort desc | sort name by col desc as result |

| Limit | limit name 10 as result |

| Mutate | mutate name add new = col \* 2 as result |

| Rename | rename name old to new as result |

| Select | select col1, col2 from name as result |

| Cast | cast name col as string as result |

| Group | group name by col \[count(col) as n] as result |

| Sample | sample name 50% as result |

| Distinct | distinct name as result |

| Join | join a with b on col as result |

| Union | union a with b as result |

| Variable | let x = 10 |

| Function | func f(x) = x \* 2 |

| For loop | for row in table { print table } |

| If/else | if x == 1 { write table into "out.json" } |

| Chart | chart raw val by label as bar into "chart.html" |

| Train | train data predict target using linear\_regression as model |

| Predict | predict data using model as output |

| Write CSV | write name into "out.csv" |

| Write JSON | write name into "out.json" |



\## Project Structure



dapine/

├── dapine.py (Main entry)

├── repl.py (Interactive REPL)

├── lexer.py (Tokenizer)

├── parser.py (Parser)

├── ast\_nodes.py (AST nodes)

├── interpreter.py (Interpreter)

├── runtime.py (Runtime engine)

├── errors.py (Error handling)

├── charts.py (Chart generation)

├── ml\_engine.py (Machine learning)

├── db\_engine.py (Database backend)

└── examples/

&#x20;   ├── hello.dap (First program)

&#x20;   ├── test\_all.dap (Full test suite)

&#x20;   ├── chart\_test.dap (Chart demo)

&#x20;   └── ml\_test.dap (ML demo)



\## Built by



A 13-year-old developer. Still growing!



\## Star this repo if you like it!

