import os
import sqlite3


def get_inventory_context() -> tuple[str, str]:
    db_path = os.environ.get("INVENTORY_DB_PATH")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='inventory'"
        )
        schema_result = cursor.fetchone()

        if schema_result is None:
            raise ValueError("Could not find 'inventory' table in database.")

        schema = schema_result[0]

        cursor.execute("SELECT * FROM inventory LIMIT 3")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

    sample_rows = "\n".join(
        ["\t".join(columns)] + ["\t".join(str(value) for value in row) for row in rows]
    )

    return schema, sample_rows
