# test_db_connection.py
import json
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sql_connection.sqlalchemy_authentication import db

def test_connection():
    print("Testing database connection...")

    try:
        # Simple check: run SELECT 1
        with db._engine.connect() as conn:  # using the underlying SQLAlchemy engine
            result = conn.exec_driver_sql("SELECT 1 AS test_value")
            row = result.fetchone()
            print("Connection test successful! Result:", row._asdict())
    except Exception as e:
        print("❌ Database connection failed:", e)

    try:
        # Optional: check if Trades table is accessible
        with db._engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT TOP (1) * FROM TransactionTrades")
            row = result.fetchone()
            if row:
                print("Trades table accessible! First row:")
                print(dict(row._mapping))
            else:
                print("Trades table is empty but accessible.")
    except Exception as e:
        print("⚠️ Could not query Trades table:", e)

if __name__ == "__main__":
    test_connection()
