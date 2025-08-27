import json
from typing import Annotated, List, Dict, Any

from semantic_kernel.functions import kernel_function
from sql_connection.sqlalchemy_authentication import db, _validate_sql, _enforce_single_table
from sqlalchemy import text

class RunSQLLangchain:
    @kernel_function(
        name="sql_retriever",
        description=(
            "Execute a read-only T-SQL SELECT against the single allowed table. "
            "Input is the full SQL string. Returns rows as JSON (list of objects). "
            "Dialect: Azure SQL (T-SQL). Table: TransactionTrades only."
        )
    )
    def run_sql_query(
        self,
        query: Annotated[str, "A complete T-SQL SELECT statement against the 'TransactionTrades' table only."]
    ) -> str:
        """
        Validates and executes a SELECT query against Azure SQL DB via LangChain SQLDatabase.
        Returns JSON string: [{"col": value, ...}, ...]
        """
        try:
            _validate_sql(query)
            _enforce_single_table(query)

            rows: List[Dict[str, Any]] = []
            # Use SQLAlchemy engine under LangChain DB to get column names reliably
            with db._engine.connect() as conn:  # type: ignore[attr-defined]
                cursor = conn.exec_driver_sql(query)
                columns = [d[0] for d in cursor.cursor.description]
                for r in cursor.fetchall():
                    rows.append({columns[i]: r[i] for i in range(len(columns))})

            return json.dumps(rows, default=str)
        except Exception as e:
            return json.dumps({"error": f"SQL execution error: {e}"})
