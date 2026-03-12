"""
DB Migration Script — v2
Recreates the meetings table with the correct schema (Integer autoincrement id).
Existing rows are preserved by copying them into the new table.

Run once after upgrading db_models.py:
    cd backend
    python migrate_db.py
"""
import sqlite3
import os
import json

db_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'meetings.db')
)
print(f"Database: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ── 1. Check existing columns ──────────────────────────────────────────────
cols = [row[1] for row in cur.execute("PRAGMA table_info(meetings)").fetchall()]
print(f"Existing columns: {cols}")

id_type = next((row[2] for row in cur.execute("PRAGMA table_info(meetings)").fetchall() if row[1] == 'id'), None)
print(f"id column type: {id_type}")

if id_type and 'INTEGER' in id_type.upper():
    print("Schema is already correct (INTEGER id). No migration needed.")
    conn.close()
    exit(0)

# ── 2. Back up existing rows ───────────────────────────────────────────────
print("Backing up existing rows...")
rows = cur.execute("SELECT * FROM meetings").fetchall()
print(f"Found {len(rows)} existing rows to preserve.")

# ── 3. Drop old table, create new one ─────────────────────────────────────
print("Dropping old meetings table...")
cur.execute("DROP TABLE IF EXISTS meetings")

print("Creating new meetings table with correct schema...")
cur.execute("""
CREATE TABLE meetings (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    DEFAULT 'Untitled Meeting',
    filename          TEXT,
    duration_seconds  INTEGER DEFAULT 0,
    upload_timestamp  DATETIME,
    created_at        DATETIME,
    transcript        TEXT,
    summary           TEXT,
    cleaning_used     INTEGER DEFAULT 0,
    key_points        TEXT,
    action_items      TEXT,
    speakers          TEXT,
    segments          TEXT,
    insights          TEXT    DEFAULT '{}',
    role_summaries    TEXT    DEFAULT '{}',
    inferred_agenda   TEXT,
    roadmap           TEXT
)
""")

# ── 4. Re-insert old rows (skip the old string id) ────────────────────────
new_cols = [
    'title','filename','duration_seconds','upload_timestamp','created_at',
    'transcript','summary','cleaning_used','key_points','action_items',
    'speakers','segments','insights','role_summaries','inferred_agenda','roadmap'
]

inserted = 0
for row in rows:
    row_dict = dict(row)
    values = [row_dict.get(c) for c in new_cols]
    cur.execute(
        f"INSERT INTO meetings ({','.join(new_cols)}) VALUES ({','.join(['?']*len(new_cols))})",
        values
    )
    inserted += 1

conn.commit()
conn.close()
print(f"Migration complete! Preserved {inserted} rows. New schema uses INTEGER autoincrement id.")
