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

def verify_real_model():
    print("Starting REAL model verification...")
    transcript = "We decide to launch tomorrow. I agree with this plan. But I disagree with the budget."
    
    print("Calling extract_insights (this may take time to download model)...")
    insights = intelligence_service.extract_insights(transcript)
    
    print(f"Insights: {insights}")
    
    if len(insights["decisions"]) > 0:
        print("✅ Decisions extracted")
    else:
        print("❌ Decisions missing")
        
    if len(insights["agreements"]) > 0:
        print("✅ Agreements extracted")
    else:
        print("❌ Agreements missing")
        
    if len(insights["conflicts"]) > 0:
        print("✅ Conflicts extracted")
    else:
        print("❌ Conflicts missing")

if __name__ == "__main__":
    verify_real_model()
