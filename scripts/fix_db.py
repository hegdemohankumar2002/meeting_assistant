import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "meetings.db")

def fix_database():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    print(f"Checking database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(meetings)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "created_at" not in columns:
            print("Adding missing column 'created_at'...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN created_at TIMESTAMP DEFAULT NULL")
            conn.commit()
            print("Column 'created_at' added.")
        
        if "inferred_agenda" not in columns:
            print("Adding missing column 'inferred_agenda'...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN inferred_agenda TEXT DEFAULT NULL")
            conn.commit()
            print("Column 'inferred_agenda' added.")

        if "roadmap" not in columns:
            print("Adding missing column 'roadmap'...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN roadmap TEXT DEFAULT NULL")
            conn.commit()
            print("Column 'roadmap' added.")

    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
