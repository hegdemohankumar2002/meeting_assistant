
import sqlite3
import os
import uuid
import datetime
import json

DB_PATH = os.path.join("data", "meetings.db")

def text_seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check columns helper
    cursor.execute("PRAGMA table_info(meetings)")
    cols = [info[1] for info in cursor.fetchall()]
    print(f"Columns: {cols}")

    # Data
    m_id = str(uuid.uuid4())
    filename = "Project_Apollo_Sync.mp3"
    upload_ts = datetime.datetime.now().isoformat()
    transcript = "Sarah: Finalize launch date. John: Backend 90% done. Fix auth bug by Friday. David: Dashboard implemented. Sarah: Launch marketing March 1st. Code freeze Feb 25th. AWS for cloud."
    
    insights = {
        "summary": "Project Apollo iOS launch discussed. Backend 90% done, auth fix due Friday. Code freeze Feb 25.",
        "key_points": ["Marketing starts March 1", "Code freeze Feb 25"],
        "action_items": ["John to fix auth bug by Friday", "John to send AWS budget request"],
        "decisions": ["AWS selected", "Code freeze Feb 25"],
        "risks": ["API delays"],
        "role_summaries_data": {"executive": "Launch on track.", "technical": "Auth bug is priority."}
    }
    
    # Insert using raw SQL
    # "cleaning_used", "speakers", "segments" might be missing if migration failed? 
    # Let's construct query dynamically based on what exists
    
    data_map = {
        "id": m_id,
        "filename": filename,
        "upload_timestamp": upload_ts,
        "created_at": upload_ts,
        "transcript": transcript,
        "summary": insights["summary"],
        # Skip complex JSONs if they cause issues, just stringify everything
        "key_points": json.dumps(insights["key_points"]),
        "action_items": json.dumps(insights["action_items"]),
        "inferred_agenda": "Project Apollo Launch",
        # Force default int for cleaning_used
        "cleaning_used": 1
    }
    
    # Filter data_map to only include columns that actually exist in DB
    final_data = {k: v for k, v in data_map.items() if k in cols}
    
    columns = ", ".join(final_data.keys())
    placeholders = ", ".join(["?"] * len(final_data))
    values = list(final_data.values())
    
    query = f"INSERT INTO meetings ({columns}) VALUES ({placeholders})"
    
    try:
        cursor.execute(query, values)
        conn.commit()
        print("Successfully inserted sample meeting via Raw SQL.")
    except Exception as e:
        print(f"Raw insert failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    text_seed()
