import sqlite3
from pathlib import Path

# Paths
db_path = Path("data/brewcode.db")
schema_path = Path("data/schema/schema_01_ingredients_recipes.sql")

def init_db():
    # Ensure data folder exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Read schema file
    schema_sql = schema_path.read_text()

    # Connect and apply schema
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
