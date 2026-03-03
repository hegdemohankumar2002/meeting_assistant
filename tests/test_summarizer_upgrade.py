
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.summarizer import summarize_structured

# Sample dialogue-heavy text (like a meeting)
sample_text = """
so, we need to decide on the timeline for the new feature launch.
I think we should aim for next Friday. It gives us enough time for testing.
Friday seems a bit tight. The QA team is already overloaded with the bug fixes from the last sprint.
That's a valid point. What about the following Monday?
Monday works for me. It gives us the weekend as a buffer if anything goes wrong.
Agreed. Let's lock in the following Monday for the release.
Now, about the database migration. Who is handling that?
I can take care of it. I've already prepared the scripts.
Great. Make sure to back up the data before running them.
Definitely. I'll do a full snapshot tonight.
Also, we need to update the API documentation.
I'll assign that to Sarah. She has the most context on the new endpoints.
Sounds good.
"""

print("--- Starting Summarizer Test ---")
print(f"Input Text Length: {len(sample_text.split())} words")

try:
    result = summarize_structured(sample_text)
    print("\n[SUCCESS] Summarization Complete")
    print(f"Summary: {result['summary']}")
    print(f"Key Points: {result['key_points']}")
    print(f"Action Items: {result['action_items']}")
except Exception as e:
    print(f"\n[ERROR] Summarization Failed: {e}")
