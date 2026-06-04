import os
import sqlite3


def get_schema() -> str:
    db_path = os.environ.get("INVENTORY_DB_PATH")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory'"
        )
        result = cursor.fetchone()
        if result is None:
            raise ValueError("Could not find 'inventory' table.")
        return result[0]


def get_sample_rows() -> str:
    db_path = os.environ.get("INVENTORY_DB_PATH")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM inventory LIMIT 3")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
    return "\n".join(
        ["\t".join(columns)] + ["\t".join(str(v) for v in row) for row in rows]
    )