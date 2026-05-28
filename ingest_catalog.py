import pandas as pd
import sqlite3

def init_database():
    csv_file = 'auto_parts_catalog.csv'
    db_file = 'inventory.db'
    table_name = 'inventory'

    print(f"Reading {csv_file}...")
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip().str.replace(' ', '_')

    print(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)

    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    print(f"Successfully loaded {len(df)} products into the '{table_name}' table.")

    cursor = conn.cursor()
    cursor.execute(f"SELECT sku, name, vehicle_compatibility FROM {table_name} LIMIT 3")
    rows = cursor.fetchall()
    
    print("\n--- Test Query Results ---")
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    init_database()