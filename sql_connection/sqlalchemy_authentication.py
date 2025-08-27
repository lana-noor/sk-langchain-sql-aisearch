import os
import re
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text

# ---------- DB Setup ----------
load_dotenv()

server = os.getenv("SQL_SERVER")
database = os.getenv("SQL_DATABASE")
username = os.getenv("SQL_USER")
password = os.getenv("SQL_PASSWORD")

# Ensure ODBC Driver 18 is installed on the host.
db_uri = (
    f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}"
    f"?driver=ODBC+Driver+18+for+SQL+Server"
)
db = SQLDatabase.from_uri(db_uri)

import re

# Allow ONLY this table
_ALLOWED_SCHEMA = "dbo"
_ALLOWED_TABLE  = "TransactionTrades"

# match [dbo].[TransactionTrades], dbo.TransactionTrades, TransactionTrades
_TABLE_RX = re.compile(
    r"""\b(?:from|join)\s+
        (                           # capture table ref
          (?:\[[^\]]+\]|\w+)        # schema or table
          (?:\s*\.\s*(?:\[[^\]]+\]|\w+))?  # optional .table
        )
        (?:\s+as\s+\w+|\s+\w+)?     # optional alias
    """,
    re.IGNORECASE | re.VERBOSE,
)

_SINGLE_STATEMENT = re.compile(r";\s*\S", re.IGNORECASE | re.DOTALL)
_FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|TRUNCATE|EXEC|CREATE)\b", re.IGNORECASE)

def _canon(part: str) -> str:
    # remove [ ] and lower-case
    return part.strip().strip("[]").lower()

def _split_schema_table(ref: str):
    parts = [p for p in re.split(r"\s*\.\s*", ref) if p]
    if len(parts) == 1:
        return None, _canon(parts[0])             # (schema=None, table)
    return _canon(parts[0]), _canon(parts[1])     # (schema, table)

def _validate_sql(sql: str) -> None:
    s = sql.strip()
    if not s.lower().startswith("select"):
        raise ValueError("Only SELECT statements are allowed.")
    if _SINGLE_STATEMENT.search(s):
        raise ValueError("Only a single statement is allowed.")
    if _FORBIDDEN.search(s):
        raise ValueError("Read-only queries only (no DML/DDL/EXEC).")

def _enforce_single_table(sql: str) -> None:
    refs = [m.group(1) for m in _TABLE_RX.finditer(sql)]
    if not refs:
        raise ValueError("Could not detect any table in query.")

    # collect all distinct schema.table refs from FROM/JOIN
    seen = set()
    for r in refs:
        schema, table = _split_schema_table(r)
        schema = schema or "dbo"  # default schema
        seen.add(f"{schema}.{table}")

    # block joins (more than one ref) or wrong table
    allowed = f"{_ALLOWED_SCHEMA.lower()}.{_ALLOWED_TABLE.lower()}"
    if len(seen) != 1 or allowed not in seen:
        raise ValueError(f"Only the '{_ALLOWED_SCHEMA}.{_ALLOWED_TABLE}' table is permitted (no joins).")
