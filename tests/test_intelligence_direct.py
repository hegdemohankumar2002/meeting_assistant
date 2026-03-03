import os
import sys
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.join(os.getcwd(), "backend"))

import app.services.intelligence as intelligence_service

# Mock the zero-shot pipeline
class MockZeroShot:
    def __call__(self, candidates, labels, multi_label=False):
        print(f"DEBUG: Mock called with candidates: {candidates}")
        logger.info(f"DEBUG: Mock called with candidates: {candidates}")
        # Return a list of results, one for each candidate
        results = []
        for text in candidates:
            if "decide" in text:
                results.append({'labels': ['decision'], 'scores': [0.9], 'sequence': text})
            elif "agree" in text:
                results.append({'labels': ['agreement'], 'scores': [0.9], 'sequence': text})
            elif "disagree" in text:
                results.append({'labels': ['conflict'], 'scores': [0.9], 'sequence': text})
            else:
                results.append({'labels': ['neutral'], 'scores': [0.9], 'sequence': text})
        return results

def mock_get_pipeline():
    return MockZeroShot()

# Patch the service
intelligence_service.get_zero_shot_pipeline = mock_get_pipeline

def test_direct_intelligence():
    print("Starting direct test...")
    transcript = "We decide to launch tomorrow. I agree with this plan. But I disagree with the budget."
    
    print("Calling extract_insights...")
    insights = intelligence_service.extract_insights(transcript)
    
    print(f"Insights: {insights}")
    logger.info(f"Insights: {insights}")
    
    if not insights["conflicts"]:
        print("DEBUG: Conflicts list is empty!")
        logger.info("DEBUG: Conflicts list is empty!")

    assert len(insights["decisions"]) > 0
    assert "We decide to launch tomorrow" in insights["decisions"][0]
    assert len(insights["agreements"]) > 0
    assert len(insights["conflicts"]) > 0
    
    print("Test Passed!")

if __name__ == "__main__":
    test_direct_intelligence()
