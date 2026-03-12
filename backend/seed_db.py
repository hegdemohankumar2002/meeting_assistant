"""
Script to seed the database with a high-quality, fully detailed sample meeting.
This populates all fields correctly so the UI can demonstrate its full capabilities.
"""
import os
import json
from datetime import datetime
from app.database import SessionLocal
from app.models.db_models import Meeting

def create_sample_meeting():
    db = SessionLocal()
    
    # ── 1. Create realistic transcript with segments ──
    transcript_text = (
        "Sarah (Product): Alright everyone, let's get started with the Project Apollo AI Integration Review. "
        "The goal today is to finalize our LLM strategy and unblock the frontend team. "
        "David, can you give us the technical update? "
        "David (Engineering): Sure. We've evaluated both Llama 3 and DeepSeek-R1. "
        "Llama 3 is faster for base tasks, but DeepSeek-R1 is giving us much better reasoning for complex queries. "
        "The problem is DeepSeek requires 5.5GB of RAM, which might be tight for our minimum spec users. "
        "Sarah (Product): That's a valid concern. What if we use Llama 3 as the default, and allow users to opt-in to DeepSeek if they have the hardware? "
        "David (Engineering): We can do that. It will take about an extra week to build the model-switching logic into the settings page. "
        "Michael (Design): From a UI perspective, I can add a hardware check on the settings page that shows a warning if they try to switch without enough RAM. I'll need the exact RAM requirements from you, David. "
        "David (Engineering): I'll send you the spec sheet by end of day. "
        "Sarah (Product): Excellent. Let's agree on that path. Llama 3 default, DeepSeek optional. "
        "One other thing, the executive team wants a timeline for the Beta launch. Are we still on track for Q3? "
        "David (Engineering): Yes, if we finalize this model decision today, the backend is 90% there. We just need the UI integrated. "
        "Sarah (Product): Great. Let's aim for a code freeze by August 15th."
    )

    segments = [
        {"start": 0.0, "end": 8.5, "speaker_id": "SPEAKER_00", "text": "Alright everyone, let's get started with the Project Apollo AI Integration Review. The goal today is to finalize our LLM strategy and unblock the frontend team. David, can you give us the technical update?"},
        {"start": 9.0, "end": 20.0, "speaker_id": "SPEAKER_01", "text": "Sure. We've evaluated both Llama 3 and DeepSeek-R1. Llama 3 is faster for base tasks, but DeepSeek-R1 is giving us much better reasoning for complex queries. The problem is DeepSeek requires 5.5GB of RAM, which might be tight for our minimum spec users."},
        {"start": 21.0, "end": 28.0, "speaker_id": "SPEAKER_00", "text": "That's a valid concern. What if we use Llama 3 as the default, and allow users to opt-in to DeepSeek if they have the hardware?"},
        {"start": 28.5, "end": 35.0, "speaker_id": "SPEAKER_01", "text": "We can do that. It will take about an extra week to build the model-switching logic into the settings page."},
        {"start": 36.0, "end": 45.0, "speaker_id": "SPEAKER_02", "text": "From a UI perspective, I can add a hardware check on the settings page that shows a warning if they try to switch without enough RAM. I'll need the exact RAM requirements from you, David."},
        {"start": 46.0, "end": 48.0, "speaker_id": "SPEAKER_01", "text": "I'll send you the spec sheet by end of day."},
        {"start": 49.0, "end": 60.0, "speaker_id": "SPEAKER_00", "text": "Excellent. Let's agree on that path. Llama 3 default, DeepSeek optional. One other thing, the executive team wants a timeline for the Beta launch. Are we still on track for Q3?"},
        {"start": 61.0, "end": 67.0, "speaker_id": "SPEAKER_01", "text": "Yes, if we finalize this model decision today, the backend is 90% there. We just need the UI integrated."},
        {"start": 68.0, "end": 72.0, "speaker_id": "SPEAKER_00", "text": "Great. Let's aim for a code freeze by August 15th."}
    ]

    speakers = [
        {"id": "SPEAKER_00", "label": "Sarah (Product)", "color": "#ec4899"},
        {"id": "SPEAKER_01", "label": "David (Engineering)", "color": "#3b82f6"},
        {"id": "SPEAKER_02", "label": "Michael (Design)", "color": "#10b981"}
    ]

    # ── 2. Create rich metadata ──
    key_points = [
        "Evaluated Llama 3 vs DeepSeek-R1 for local AI features.",
        "DeepSeek provides better reasoning but has higher RAM requirements (5.5GB).",
        "Team finalized a dual-model strategy to balance performance and hardware limits.",
        "Beta launch remains on track for Q3 with an upcoming code freeze."
    ]

    action_items = [
        "David — Send hardware specification sheet to Design — End of Day",
        "Michael — Implement hardware validation warning on the settings page UI — Next Week",
        "David — Build model-switching capabilities into the backend — Next Week"
    ]

    # Structure matches what summarizer.py outputs now
    insights = {
        "decisions": [
            "Llama 3 will be the default model for minimum spec compatibility.",
            "DeepSeek-R1 will be offered as an opt-in for power users.",
            "Code freeze is officially scheduled for August 15th."
        ],
        "agreements": [
            "All agreed that enforcing a 5.5GB hard requirement is too risky for user adoption.",
            "Agreed that the Beta launch timeline is safe for Q3."
        ],
        "conflicts": [
            "None recorded. Minor concern over taking an extra week to build switching logic, but accepted."
        ]
    }

    role_summaries = {
        "executive": "The technical strategy is secured for the Q3 Beta launch. Llama 3 will serve as the baseline AI model to guarantee broad hardware compatibility, while DeepSeek will be offered to power users. Code freeze set for mid-August.",
        "technical": "We will implement a dual-model architecture. Llama 3 is default. A hardware check must be written in the frontend to validate RAM before downloading the 5.5GB DeepSeek model. Backend API needs a new route to toggle active models."
    }

    roadmap = (
        "**Phase 1: Implementation (Next 1-2 Weeks)**\\n"
        "- Backend: Build model toggle API.\\n"
        "- Frontend: Build RAM validation UI.\\n\\n"
        "**Phase 2: QA & Polish (July - August)**\\n"
        "- Extensive testing on low-end machines.\\n\\n"
        "**Phase 3: Code Freeze (August 15)**\\n"
        "- Lock down features, prep Beta release candidates."
    )

    summary = (
        "The team reviewed the LLM integration strategy for Project Apollo. "
        "To balance performance with high reasoning capabilities, the team decided to make Llama 3 "
        "the default model, while offering DeepSeek-R1 as an optional toggle for users with superior hardware. "
        "The project remains on track for a Q3 Beta launch, with a code freeze scheduled for August 15th."
    )

    # ── 3. Insert Database Record ──
    meeting = Meeting(
        title="Project Apollo: AI Integration Review",
        filename="apollo_ai_review.wav",
        duration_seconds=72,
        upload_timestamp=datetime.utcnow(),
        created_at=datetime.utcnow(),
        transcript=transcript_text,
        summary=summary,
        cleaning_used=1,
        key_points=json.dumps(key_points),
        action_items=json.dumps(action_items),
        speakers=json.dumps(speakers),
        segments=json.dumps(segments),
        insights=json.dumps(insights),
        role_summaries=json.dumps(role_summaries),
        inferred_agenda="Subject: Project Apollo - Finalizing LLM Strategy",
        roadmap=roadmap
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    db.close()
    
    print(f"Sample meeting '{meeting.title}' successfully inserted with ID: {meeting.id}")

if __name__ == "__main__":
    create_sample_meeting()
