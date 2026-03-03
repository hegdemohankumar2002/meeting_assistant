
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import SessionLocal
from app.services.query_engine import query_meeting_memory

def debug():
    print("Debug: Starting chat test...")
    db = SessionLocal()
    try:
        response = query_meeting_memory("What happened in the last meeting?", db)
        print(f"Response: {response}")
    except Exception as e:
        print("CRITICAL ERROR CAUGHT:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug()
