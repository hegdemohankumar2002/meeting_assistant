import os
import sys
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.join(os.getcwd(), "backend"))

import app.services.summarizer as summarizer_service

# Mock summarize_text to return the input (identity) so we can verify what was passed
def mock_summarize_text(text):
    return f"SUMMARY: {text[:50]}..."

summarizer_service.summarize_text = mock_summarize_text

def test_role_summaries():
    print("Starting role summary test...")
    
    transcript = (
        "Welcome everyone. We need to decide on the database. "
        "I think PostgreSQL is better than MySQL. "
        "Agreed, let's use Postgres. "
        "Also, the API endpoint /users is failing with a 500 error. "
        "We need to fix the Python code in the backend. "
        "So, we decided to use Postgres. Meeting adjourned."
    )
    
    insights = {
        "decisions": ["We decided to use Postgres"],
        "agreements": ["Agreed, let's use Postgres"],
        "conflicts": []
    }
    
    print("Generating role summaries...")
    summaries = summarizer_service.generate_role_summaries(transcript, insights)
    
    print(f"Executive: {summaries['executive']}")
    print(f"Technical: {summaries['technical']}")
    
    # Verify Executive contains decisions
    assert "decided" in summaries['executive'].lower()
    
    # Verify Technical contains technical terms
    assert "postgresql" in summaries['technical'].lower() or "postgres" in summaries['technical'].lower()
    assert "api" in summaries['technical'].lower()
    assert "python" in summaries['technical'].lower()
    
    print("Test Passed!")

if __name__ == "__main__":
    test_role_summaries()
