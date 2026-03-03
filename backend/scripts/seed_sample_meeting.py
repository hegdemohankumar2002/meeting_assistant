
import sys
import os
import json
from datetime import datetime
import uuid

# Add backend to path to import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.database import SessionLocal
from app.models.db_models import Meeting

def seed_data():
    db = SessionLocal()
    
    # 1. Define Sample Meeting Data (Project Apollo)
    sample_transcript = """
    [00:00:05] Sarah: Alright everyone, Sara here. Let's get started with the Project Apollo weekly sync. 
    [00:00:10] John: Hi Sarah, I'm here. David is joining in a minute.
    [00:00:15] Sarah: Great. The main goal today is to finalize the launch date for the iOS app.
    [00:00:30] David: Hey guys, sorry I'm late.
    [00:00:35] Sarah: No worries David. We were just discussing the timeline. 
    [00:01:00] John: Currently, the backend API is 90% done. We just need to fix the authentication bug in the login flow.
    [00:01:20] David: For the frontend, the new dashboard design is implemented. But we are waiting on the API to connect the real data.
    [00:02:00] Sarah: Okay. We cannot delay the launch. The marketing campaign starts on March 1st.
    [00:02:45] John: I can have the auth bug fixed by this Friday. 
    [00:03:00] Sarah: Perfect. Then let's set the internal code freeze for next Wednesday, February 25th.
    [00:03:15] David: Agreed. I'll make sure the dashboard is tested with mock data by then.
    [00:04:00] Sarah: One more thing. We need to decide on the cloud provider. AWS or Azure?
    [00:04:20] John: Given our team's expertise, I vote for AWS. verify_map_reduce.pyIt will save us setup time.
    [00:04:30] David: I agree. AWS has better support for the lambda functions we are using.
    [00:04:45] Sarah: It's decided then. We stick with AWS. John, please send the budget approval request for the new EC2 instances.
    [00:05:00] John: Will do. I'll send it to finance by EOD tomorrow.
    [00:05:15] Sarah: Great meeting everyone. Let's get back to work.
    """
    
    # Structured Insights (what the AI would generate)
    insights_data = {
        "summary": "The team discussed the Project Apollo iOS app launch. The backend is 90% complete, pending an auth bug fix. Frontend is waiting on API integration. The team agreed on a code freeze for Feb 25th and finalized AWS as the cloud provider.",
        "key_points": [
            "Project Apollo iOS launch is the primary focus.",
            "Backend API is 90% complete; Authentication bug needs fixing.",
            "Marketing campaign begins March 1st.",
            "Internal code freeze set for Wednesday, Feb 25th.",
            "AWS selected as cloud provider due to team expertise and Lambda support."
        ],
        "action_items": [
            "John to fix authentication bug by this Friday.",
            "David to test dashboard with mock data by Feb 25th.",
            "John to send AWS budget approval request to finance by EOD tomorrow."
        ],
        "decisions": [
            "Internal code freeze date set for Feb 25th.",
            "Selected AWS as the cloud infrastructure provider."
        ],
        "risks": [
            "Risk: API delays could block frontend integration -> Mitigation: Mock data testing."
        ],
        "role_summaries_data": {
            "executive": "Project Apollo is on track for March 1st marketing launch. Key decisions: AWS selected for infrastructure (budget approval pending) and code freeze set for Feb 25th.",
            "technical": "Backend focus is resolving the Auth bug by Friday. Frontend will proceed with mock data testing until API integration. Infrastructure will be AWS-based."
        }
    }

    # Create Meeting Object
    meeting = Meeting(
        id=str(uuid.uuid4()),
        filename="Project_Apollo_Sync.mp3",
        upload_timestamp=datetime.now(),
        transcript=sample_transcript,
        # Flattened fields
        summary=insights_data["summary"],
        key_points=json.dumps(insights_data["key_points"]),
        action_items=json.dumps(insights_data["action_items"]),
        # JSON fields
        insights=json.dumps(insights_data),
        role_summaries=json.dumps(insights_data["role_summaries_data"]),
        inferred_agenda="Subject: Project Apollo Launch - iOS App & Infrastructure",
        roadmap="Phase 1: Fix Auth Bug (Fri)\nPhase 2: Code Freeze (Feb 25)\nPhase 3: Launch (Mar 1)",
        cleaning_used=1 # Validated schema
    )

    try:
        db.add(meeting)
        db.commit()
        print(f"Successfully seeded meeting: {meeting.inferred_agenda}")
        print(f"ID: {meeting.id}")
    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
