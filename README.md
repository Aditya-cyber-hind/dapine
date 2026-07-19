\# Dapine — Data Pipeline Language



!\[Python](https://img.shields.io/badge/Python-3.x-blue)

!\[License](https://img.shields.io/badge/License-MIT-green)

!\[Status](https://img.shields.io/badge/Status-Active-success)



A lightweight \*\*data pipeline programming language\*\* built in Python.



Dapine lets you read, transform, analyze, visualize, and export data using a simple, readable syntax. It supports data processing, statistics, charts, machine learning workflows, and an interactive REPL environment.



> Built by a 13-year-old developer exploring programming and language design.



\---



\## 📌 About Dapine



Dapine is a \*\*domain-specific language (DSL)\*\* for creating data pipelines.



It allows users to describe complete workflows:



```

Read → Transform → Analyze → Visualize → Export

```



Instead of writing long scripts, Dapine provides a clean syntax for handling data tasks.



\---



\# ✨ Features



\## 📂 Data Handling



\- Read and write CSV files

\- Read and write JSON files

\- Join tables

\- Union datasets

\- Database backend support



\## 🔄 Data Transformation



\- Filter rows with comparisons and string matching

\- Sort data

\- Limit results

\- Sample datasets

\- Remove duplicate rows

\- Create new columns using `mutate`

\- Rename columns

\- Select columns

\- Cast data types



\## 📊 Analytics



\- Group by operations

\- Count, sum, average, minimum, maximum

\- Mean, median, and standard deviation statistics



\## 🧠 Programming Features



\- Custom functions with `func`

\- Variables with `let`

\- Loops with `for`

\- Conditional logic with `if/else`



\## 🔤 String Functions



\- `upper`

\- `lower`

\- `length`

\- `trim`

\- `concat`



\## ➕ Math Functions



\- `abs`

\- `round`

\- `sqrt`

\- `ceil`

\- `floor`



\## 📅 Date Functions



\- `today`

\- `year`

\- `month`

\- `date\_add`

\- `date\_diff`



\## 📈 Visualization



Generate browser-based charts:



\- Bar charts

\- Pie charts

\- Line charts

\- Scatter plots

\- Radar charts



\## 🤖 Machine Learning



Create machine learning workflows:



\- Train models

\- Make predictions

\- Linear regression support



\## 🔍 Developer Features



\- Transformation lineage tracking

\- Interactive REPL mode

\- Custom error handling



\---



\# 🚀 Quick Start



\## Clone Repository



```bash

git clone https://github.com/Aditya-cyber-hind/dapine.git

cd dapine

```



\## Install Dependencies



```bash

pip install duckdb scikit-learn

```



\## Run Dapine



```bash

python dapine.py examples/test\_all.dap

```



\## Start REPL



```bash

python repl.py

```



\---



\# 📝 Example



```dapine

func double(x) = x \* 2



pipeline example() {



&#x20;   read "data.csv" as raw



&#x20;   print raw



&#x20;   stats raw



&#x20;   filter raw where age >= 18 as adults



&#x20;   mutate adults add double\_age = double(age) as with\_age



&#x20;   group with\_age by city \[

&#x20;       count(name) as users,

&#x20;       avg(age) as avg\_age

&#x20;   ] as report



&#x20;   sort report by users desc as final



&#x20;   write final into "report.json"



&#x20;   chart final users by city as bar into "chart.html"

}

```



\---



\# 🤖 Machine Learning Example



```dapine

pipeline ml\_example() {



&#x20;   read "houses.csv" as data



&#x20;   train data predict price 

&#x20;   using linear\_regression 

&#x20;   as model



&#x20;   read "new\_houses.csv" as new\_data



&#x20;   predict new\_data using model 

&#x20;   as estimated\_price



&#x20;   write estimated\_price 

&#x20;   into "predictions.json"

}

```



\---



\# 💻 REPL Mode



Run commands interactively:



```text

dap> read "data.csv" as raw



dap> print raw



dap> filter raw where age > 18 as adults



dap> stats adults



dap> chart adults age by name as bar into "chart.html"



dap> /tables



dap> /lineage



dap> /exit

```



\---



\# 📁 Project Structure



```

dapine/

│

├── dapine.py          # Main entry point

├── repl.py            # Interactive REPL

├── lexer.py           # Tokenizer

├── parser.py          # Parser

├── ast\_nodes.py       # AST nodes

├── interpreter.py     # Interpreter

├── runtime.py         # Runtime engine

├── errors.py          # Error handling

├── charts.py          # Chart generator

├── ml\_engine.py       # Machine learning engine

├── db\_engine.py       # Database backend

│

└── examples/

&#x20;   └── Example pipelines

```



\---



\# 🛣️ Roadmap



Future improvements:



\- \[ ] More machine learning algorithms

\- \[ ] Streaming data pipelines

\- \[ ] Parallel execution

\- \[ ] Plugin system

\- \[ ] Better error messages

\- \[ ] Package manager for Dapine libraries



\---



\# 🤝 Contributing



Suggestions, bug reports, and contributions are welcome.



Feel free to open issues or submit pull requests.



\---



\# 📜 License



MIT License



\---



\# 👨‍💻 Built By



\*\*Aditya\*\*



A young developer exploring programming, data, and language design.

