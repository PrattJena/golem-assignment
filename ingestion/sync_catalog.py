import os
import sqlite3
import gspread
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def init_database():
    credentials_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    db_path = os.getenv("INVENTORY_DB_PATH", "inventory.db")

    print("Fetching data from Google Sheets...")
    gc = gspread.service_account(filename=credentials_path)
    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.sheet1

    rows = worksheet.get_all_records()
    df = pd.DataFrame(rows)
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS inventory")
    cursor.execute("""
        CREATE TABLE inventory (
            sku TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            price REAL,
            stock_quantity INTEGER,
            key_specs TEXT,
            description TEXT,
            vehicle_compatibility TEXT,
            aisle_location TEXT
        )
    """)

    df.to_sql("inventory", conn, if_exists="append", index=False)

    print(f"Successfully loaded {len(df)} products into the 'inventory' table.")

    cursor.execute("SELECT sku, name, category FROM inventory LIMIT 3")
    rows = cursor.fetchall()

    print("\n--- Test Query Results ---")
    for row in rows:
        print(row)
    
    print("=" * 50)

    conn.close()


if __name__ == "__main__":
    init_database()