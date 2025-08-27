# tests/test_sql_plugin.py
import json
import sys, os
# ensure project root is on sys.path when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sk_plugins.langchain_sql_db import RunSQLLangchain  # adjust if your path differs

def test_sql():
    sql_plugin = RunSQLLangchain()

    query = """
    SELECT TOP (5) TradeID, TradeDate, InstrumentName, Quantity, NetAmount
    FROM [dbo].[TransactionTrades]
    ORDER BY TradeDate DESC
    """

    print("Running query:\n", query)
    result = sql_plugin.run_sql_query(query)

    try:
        parsed = json.loads(result)
        if isinstance(parsed, dict) and "error" in parsed:
            print("\nPlugin returned error:")
            print(parsed["error"])
        else:
            print("\nResults (parsed JSON):")
            for row in parsed:
                print(row)
    except Exception:
        print("\nRaw result string:")
        print(result)

if __name__ == "__main__":
    test_sql()
