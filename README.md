\# Dapine - Data Pipeline Language



A data pipeline language built in Python by a 13-year-old developer.



\## What it does



Dapine reads CSV/JSON files, transforms data, and outputs results. It has machine learning, charts, and an interactive REPL mode.



\## Quick Start



git clone https://github.com/Aditya-cyber-hind/dapine.git

cd dapine

pip install duckdb scikit-learn

python dapine.py examples/test\_all.dap

python repl.py



\## Features



\- Read/write CSV and JSON files

\- Filter data with comparisons and string matching

\- Sort, limit, sample, and deduplicate rows

\- Create new columns with mutate

\- Rename, select, and cast columns

\- Group by with count, sum, avg, min, max

\- Join and union tables

\- Statistics (mean, median, stdev)

\- Custom functions with func

\- Variables with let

\- Loops with for

\- Conditional logic with if/else

\- String functions (upper, lower, length, trim, concat)

\- Math functions (abs, round, sqrt, ceil, floor)

\- Date functions (today, year, month, date\_add, date\_diff)

\- Charts that open in your browser (bar, pie, line, scatter, radar)

\- Machine learning (train models and predict)

\- Lineage tracking for every transformation

\- Interactive REPL mode



\## Example



func double(x) = x \* 2



pipeline example() {

&#x20;   read "data.csv" as raw

&#x20;   print raw

&#x20;   stats raw

&#x20;   filter raw where age >= 18 as adults

&#x20;   mutate adults add double\_age = double(age) as with\_age

&#x20;   group with\_age by city \[count(name) as users, avg(age) as avg\_age] as report

&#x20;   sort report by users desc as final

&#x20;   write final into "report.json"

&#x20;   chart final users by city as bar into "chart.html"

}



\## Machine Learning



pipeline ml\_example() {

&#x20;   read "houses.csv" as data

&#x20;   train data predict price using linear\_regression as model

&#x20;   read "new\_houses.csv" as new\_data

&#x20;   predict new\_data using model as estimated\_price

&#x20;   write estimated\_price into "predictions.json"

}



\## REPL Commands



dap> read "data.csv" as raw

dap> print raw

dap> filter raw where age > 18 as adults

dap> stats adults

dap> chart adults age by name as bar into "chart.html"

dap> /tables

dap> /lineage

dap> /exit



\## Files



dapine.py - Main entry point

repl.py - Interactive REPL

lexer.py - Tokenizer

parser.py - Parser

ast\_nodes.py - AST nodes

interpreter.py - Interpreter

runtime.py - Runtime engine

errors.py - Error handling

charts.py - Chart generator

ml\_engine.py - Machine learning engine

db\_engine.py - Database backend

examples/ - Example pipelines



\## Built by



A 13-year-old developer learning to code.

