import sqlite3
from typing import List, Dict, Any

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM inventory")
results = cursor.fetchall()[:1]
columns = [desc[0] for desc in cursor.description] 
query_results: List[Dict[str, Any]] = [ dict(zip(columns, row)) for row in results ]
print(query_results)
conn.close()
