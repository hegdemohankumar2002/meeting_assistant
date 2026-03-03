import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import sys

load_dotenv()
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Force unbuffered stdout
sys.stdout.reconfigure(line_buffering=True)

from app.main import app
from app.database import Base, get_db
import app.services.intelligence as intelligence_service

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_intelligence.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Mock the zero-shot pipeline
class MockZeroShot:
    def __call__(self, candidates, labels, multi_label=False):
        print(f"DEBUG: Mock called with candidates: {candidates}")
        # Return a list of results, one for each candidate
        results = []
        for text in candidates:
            if "decide" in text:
                results.append({'labels': ['making a decision'], 'scores': [0.9], 'sequence': text})
            elif "agree" in text:
                results.append({'labels': ['expressing agreement'], 'scores': [0.9], 'sequence': text})
            elif "disagree" in text:
                results.append({'labels': ['expressing disagreement or conflict'], 'scores': [0.9], 'sequence': text})
            else:
                results.append({'labels': ['neutral statement'], 'scores': [0.9], 'sequence': text})
        return results

def mock_get_pipeline():
    return MockZeroShot()

intelligence_service.get_zero_shot_pipeline = mock_get_pipeline

def test_intelligence_integration():
    # Mock other heavy services
    import app.api.routes as routes
    routes.transcribe_audio = lambda *args, **kwargs: {
        "text": "We decide to launch tomorrow. I agree with this plan. But I disagree with the budget.",
        "segments": []
    }
    routes.diarize_audio = lambda *args, **kwargs: []
    routes.clean_audio = lambda i, o: i
    routes.summarize_structured = lambda t: {"summary": "summary", "key_points": [], "action_items": []}
    routes.analyze_emotion = lambda t: "neutral"

    # Create dummy file
    with open("test_audio_int.wav", "wb") as f:
        f.write(b"fake audio")

    response = client.post(
        "/transcribe/",
        files={"file": ("test_audio_int.wav", open("test_audio_int.wav", "rb"), "audio/wav")},
        data={"enable_cleaning": "false"}
    )
    
    print("Response:", response.json())
    assert response.status_code == 200
    data = response.json()
    
    # Verify insights
    insights = data["insights"]
    print(f"Insights: {insights}")
    assert len(insights["decisions"]) > 0
    assert "We decide to launch tomorrow" in insights["decisions"][0]
    assert len(insights["agreements"]) > 0
    assert len(insights["conflicts"]) > 0
    
    # Cleanup
    os.remove("test_audio_int.wav")
    if os.path.exists("test_intelligence.db"):
        os.remove("test_intelligence.db")
    print("Test Passed!")

if __name__ == "__main__":
    test_intelligence_integration()
