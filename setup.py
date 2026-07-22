from setuptools import setup

setup(
    name="dapine-lang",
    version="3.0.0",
    description="Data Pipeline Language - Transform data with simple syntax",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Aditya Choudhary",
    url="https://github.com/Aditya-cyber-hind/dapine",
    py_modules=[
        "dapine", "repl", "lexer", "parser", "ast_nodes",
        "interpreter", "runtime", "errors", "charts",
        "ml_engine", "connectors", "duck_engine", "ai_engine",
        "reports", "alerts", "scheduler", "api_server",
        "stdlib", "dapine_types", "dap_pm", "db_engine"
    ],
    install_requires=[
        "duckdb", "scikit-learn", "openpyxl", "pandas", "pyarrow", "groq"
    ],
    entry_points={
        "console_scripts": [
            "dapine=dapine:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)