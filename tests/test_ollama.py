
import sys
import os
import logging
from app.services.summarizer import summarize_structured
from app.services.intelligence import extract_insights
import json

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

# Mock transcript for testing
mock_transcript = """
My apologies there. This is the meeting of the arm of Springfield planning meeting. 
We are starting at 6pm. I'm a mayor, Patrick.
Approval of the agenda. Can I get a mover and a seconder for that to please Mark and Glenn.
And the additions are to the agenda and I see none. I get a show of hands of those in support. It's unanimous, therefore carried.
Mr. Potter is requesting Council's approval for the reduced side yard and rear yard setbacks.
If Council were to consider this variation, I would offer the following condition. Number one, that the applicant obtain the required municipal building permits.
With that being read, can I get a show of hands of those in support? That is unanimous and it is carried.
"""

def test_ollama():
    print("--- Testing Ollama Summarization (Smart Extraction) ---")
    summary = summarize_structured(mock_transcript)
    print("\nSummary Result:")
    print(json.dumps(summary, indent=2))
    
    if summary.get("summary") and summary.get("inferred_agenda"):
        print("✅ Summarization & Auto-Agenda Success")
    else:
        print("❌ Summarization Failed (Check output)")

    print("\n--- Testing Roadmap Generation ---")
    from app.services.roadmap_generator import generate_roadmap
    roadmap = generate_roadmap(summary)
    print("\nRoadmap Result:")
    print(roadmap)
    
    if "Mission Statement" in roadmap or "Strategic Milestones" in roadmap:
        print("✅ Roadmap Generation Success")
    else:
        print("❌ Roadmap Generation Failed")

if __name__ == "__main__":
    # Ensure we are in the backend directory context or path is set
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_ollama()
