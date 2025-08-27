

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sql_connection.sqlalchemy_authentication import db

def test_connection():
    print("Testing database connection...")
    with db._engine.connect() as conn:
        r = conn.exec_driver_sql("SELECT 1 AS test_value").fetchone()
        print("OK:", dict(r._mapping))
