\# Dapine - Data Pipeline Language



A simple data pipeline language built in Python. Transform CSV/JSON data with an easy-to-read syntax.



\## Features



\- Read CSV, JSON files (auto-detect format)

\- Filter with ==, !=, >, <, AND, OR, starts\_with, contains, ends\_with

\- Aggregate with group by (count, sum, avg, min, max)

\- Transform with mutate, rename, select, cast

\- Stats - min, max, mean, median, stdev

\- String functions - upper, lower, length, trim, concat

\- Math functions - abs, round, sqrt, ceil, floor

\- Write CSV, JSON output

\- Lineage tracking - know where every value came from

\- REPL mode - interactive data exploration

\- Custom functions with func

\- Control flow - let, for, if/else



\## Quick Start



git clone https://github.com/Aditya-cyber-hind/dapine.git

cd dapine

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



Read CSV:   read "file.csv" as name

Print:      print name

Stats:      stats name

Filter:     filter name where col > 10 as result

Sort:       sort name by col asc as result

Limit:      limit name 10 as result

Mutate:     mutate name add new = col \* 2 as result

Rename:     rename name old to new as result

Select:     select col1, col2 from name as result

Cast:       cast name col as string as result

Group:      group name by col \[count(col) as n] as result

Sample:     sample name 50% as result

Distinct:   distinct name as result

Join:       join a with b on col as result

Union:      union a with b as result

Variable:   let x = 10

Function:   func f(x) = x \* 2

For loop:   for row in table { print table }

If/else:    if x == 1 { write table into "out.json" }

Write CSV:  write name into "out.csv"

Write JSON: write name into "out.json"



\## Built by



A 13-year-old learning to code. Still growing!

