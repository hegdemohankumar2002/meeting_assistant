from fastapi import APIRouter, UploadFile, File, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import json
import time
from app.services.transcription import transcribe_audio, transcribe_audio_chunked
from app.services.summarizer import summarize_text, summarize_structured, generate_role_summaries
from app.services.cleaner import clean_audio
from app.services.diarization import diarize_audio
from app.services.intelligence import extract_insights
from app.services.roadmap_generator import generate_roadmap
from app.database import get_db
from app.models.db_models import Meeting
from sqlalchemy.orm import Session
from sqlalchemy import or_

router = APIRouter()

# --- Speaker Color Palette ---
SPEAKER_COLORS = [
    "#6366f1",  # Indigo
    "#22d3ee",  # Cyan
    "#f59e0b",  # Amber
    "#10b981",  # Emerald
    "#f43f5e",  # Rose
    "#a855f7",  # Purple
    "#3b82f6",  # Blue
    "#fb923c",  # Orange
]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file and return server path for streaming processing.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        return {"file_path": tmp_path, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe/chunk")
async def transcribe_chunk(file: UploadFile = File(...)):
    """
    Fast transcription for small live-audio chunks to provide accurate real-time captions.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        # Use 'tiny' model for a very fast punctuation-rich live caption pass to prevent CPU hanging
        transcription_result = transcribe_audio(tmp_path, model_size="tiny")
        os.remove(tmp_path)
        
        return {"text": transcription_result["text"]}
    except Exception as e:
        return {"text": "", "error": str(e)}


def align_segments(whisper_segments, diarization_segments):
    """
    Assign speakers to Whisper segments based on time overlap with diarization segments.
    Assigns distinct colors to each speaker.
    """
    aligned_segments = []
    speakers_map = {}  # id -> {id, label, color}

    def get_speaker(spk_label):
        if spk_label not in speakers_map:
            color_idx = len(speakers_map) % len(SPEAKER_COLORS)
            speakers_map[spk_label] = {
                "id": spk_label,
                "label": spk_label.replace("_", " ").title(),
                "color": SPEAKER_COLORS[color_idx]
            }
        return speakers_map[spk_label]

    for seg in whisper_segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]

        best_speaker = "Unknown"
        max_overlap = 0.0

        for d_seg in diarization_segments:
            d_start, d_end = d_seg["start"], d_seg["end"]
            overlap_start = max(start, d_start)
            overlap_end = min(end, d_end)
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = d_seg["speaker"]

        speaker_obj = get_speaker(best_speaker)

        aligned_segments.append({
            "start": start,
            "end": end,
            "speaker_id": speaker_obj["id"],
            "text": text.strip(),
        })

    return list(speakers_map.values()), aligned_segments


def get_audio_duration(file_path: str) -> int:
    """Get the duration of an audio file in seconds."""
    try:
        import soundfile as sf
        with sf.SoundFile(file_path) as f:
            return int(len(f) / f.samplerate)
    except Exception:
        return 0


@router.post("/transcribe/")
async def transcribe_and_summarize(
    file: UploadFile = File(...),
    title: str | None = Query(default=None, description="Meeting title"),
    language: str | None = Query(default=None, description="Force language code, e.g., 'en'"),
    model_size: str | None = Query(default=None, description="Whisper model size"),
    enable_cleaning: bool = Query(default=True, description="Enable audio denoising"),
    db: Session = Depends(get_db),
):
    print("DEBUG: Endpoint /transcribe/ hit")

    file_size_mb = 0
    try:
        file.file.seek(0, 2)
        file_size_bytes = file.file.tell()
        file.file.seek(0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        print(f"INFO: Processing file: {file.filename} ({file_size_mb:.2f} MB)")
    except Exception as e:
        print(f"WARNING: Could not determine file size: {e}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Optional cleaning
        cleaning_used = False
        if enable_cleaning:
            cleaned_path = clean_audio(tmp_path)
            if cleaned_path != tmp_path:
                cleaning_used = True
                os.remove(tmp_path)
                tmp_path = cleaned_path

        # Get duration before processing
        duration_seconds = get_audio_duration(tmp_path)

        # Transcription
        print("DEBUG: Starting transcription...")
        transcription_result = transcribe_audio(tmp_path, language=language, model_size=model_size or "small")
        transcript_text = transcription_result["text"]
        whisper_segments = transcription_result["segments"]

        # Diarization
        print("DEBUG: Starting diarization...")
        diarization_segments = diarize_audio(tmp_path)
        speakers, aligned_segments = align_segments(whisper_segments, diarization_segments)

        # Summarization
        print("DEBUG: Starting summarization...")
        structured_summary = summarize_structured(transcript_text)

        # Extract insights
        print("DEBUG: Extracting insights...")
        insights = extract_insights(transcript_text)
        if structured_summary.get("decisions"):
            insights["decisions"] = structured_summary["decisions"] + insights.get("decisions", [])
        if structured_summary.get("risks"):
            insights["risks"] = structured_summary.get("risks", [])

        # Role summaries
        role_summaries = generate_role_summaries(transcript_text, structured_summary)

        # Roadmap
        roadmap_md = generate_roadmap(structured_summary)

        # Auto-generate title if not provided
        meeting_title = title or structured_summary.get("inferred_agenda") or file.filename or "Untitled Meeting"

        # Save to database
        meeting = Meeting(
            title=meeting_title,
            filename=file.filename,
            duration_seconds=duration_seconds,
            transcript=transcript_text,
            summary=structured_summary["summary"],
            key_points=json.dumps(structured_summary["key_points"]),
            action_items=json.dumps(structured_summary["action_items"]),
            speakers=json.dumps(speakers),
            segments=json.dumps(aligned_segments),
            cleaning_used=cleaning_used,
            insights=json.dumps(insights),
            role_summaries=json.dumps(role_summaries),
            inferred_agenda=structured_summary.get("inferred_agenda", ""),
            roadmap=roadmap_md
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        os.remove(tmp_path)

        return {
            "id": meeting.id,
            "title": meeting.title,
            "duration_seconds": duration_seconds,
            "transcript": transcript_text,
            "summary": structured_summary["summary"],
            "key_points": structured_summary["key_points"],
            "action_items": structured_summary["action_items"],
            "speakers": speakers,
            "segments": aligned_segments,
            "cleaning_used": cleaning_used,
            "insights": insights,
            "role_summaries": role_summaries,
            "inferred_agenda": structured_summary.get("inferred_agenda", ""),
            "roadmap": roadmap_md,
            "decisions": structured_summary.get("decisions", []),
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time streaming transcription.
    """
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        file_path = data.get('file_path')
        language = data.get('language')
        model_size = data.get('model_size', 'small')
        enable_cleaning = data.get('enable_cleaning', True)
        title = data.get('title')

        if not file_path or not os.path.exists(file_path):
            await websocket.send_json({"error": "Invalid file path"})
            return

        duration_seconds = get_audio_duration(file_path)

        # Stage 1: Transcription
        await websocket.send_json({"stage": "transcription", "status": "started", "message": "Starting transcription..."})

        all_segments = []
        full_text = []

        for segment in transcribe_audio_chunked(file_path, language, model_size):
            all_segments.append(segment)
            full_text.append(segment["text"])
            await websocket.send_json({
                "stage": "transcription",
                "status": "progress",
                "segment": segment,
                "partial_text": " ".join(full_text)
            })

        transcript_text = " ".join(full_text)

        await websocket.send_json({"stage": "transcription", "status": "done", "text": transcript_text})

        # Stage 2: Diarization
        await websocket.send_json({"stage": "diarization", "status": "started", "message": "Identifying speakers..."})
        diarization_segments = diarize_audio(file_path)
        speakers, aligned_segments = align_segments(all_segments, diarization_segments)
        await websocket.send_json({"stage": "diarization", "status": "done", "speakers": speakers, "segments": aligned_segments})

        # Stage 3: Analysis
        await websocket.send_json({"stage": "analysis", "status": "started", "message": "Analyzing meeting content..."})

        structured_summary = summarize_structured(transcript_text)
        await websocket.send_json({"stage": "analysis", "status": "progress", "type": "summary", "data": structured_summary})

        insights = extract_insights(transcript_text)
        await websocket.send_json({"stage": "analysis", "status": "progress", "type": "insights", "data": insights})

        role_summaries = generate_role_summaries(transcript_text, structured_summary)

        # Stage 4: Roadmap
        roadmap_md = generate_roadmap(structured_summary)

        await websocket.send_json({"stage": "analysis", "status": "done", "type": "role_summaries", "data": role_summaries})

        # Auto title
        meeting_title = title or structured_summary.get("inferred_agenda") or "Untitled Meeting"

        # Save to database (now with all fields)
        meeting = Meeting(
            title=meeting_title,
            duration_seconds=duration_seconds,
            transcript=transcript_text,
            summary=structured_summary["summary"],
            key_points=json.dumps(structured_summary["key_points"]),
            action_items=json.dumps(structured_summary["action_items"]),
            speakers=json.dumps(speakers),
            segments=json.dumps(aligned_segments),
            cleaning_used=enable_cleaning,
            insights=json.dumps(insights),
            role_summaries=json.dumps(role_summaries),
            inferred_agenda=structured_summary.get("inferred_agenda", ""),
            roadmap=roadmap_md
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        await websocket.send_json({
            "stage": "complete",
            "meeting_id": meeting.id,
            "title": meeting.title,
            "roadmap": roadmap_md,
            "decisions": structured_summary.get("decisions", []),
            "message": "Processing complete!"
        })

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ─── Meeting CRUD ────────────────────────────────────────────────────────────

@router.get("/meetings/")
async def get_meetings(db: Session = Depends(get_db)):
    """Get all meetings ordered by most recent."""
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "title": m.title or "Untitled Meeting",
            "filename": m.filename,
            "duration_seconds": m.duration_seconds or 0,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "transcript_preview": m.transcript[:200] if m.transcript else "",
            "summary_preview": m.summary[:300] if m.summary else "",
            "inferred_agenda": m.inferred_agenda or "",
        }
        for m in meetings
    ]


@router.get("/meetings/search")
async def search_meetings(q: str = Query(..., description="Search query"), db: Session = Depends(get_db)):
    """Full-text keyword search across meeting transcripts, summaries, and titles."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    results = db.query(Meeting).filter(
        or_(
            Meeting.title.contains(q),
            Meeting.transcript.contains(q),
            Meeting.summary.contains(q),
            Meeting.inferred_agenda.contains(q),
        )
    ).order_by(Meeting.created_at.desc()).limit(20).all()

    return [
        {
            "id": m.id,
            "title": m.title or "Untitled Meeting",
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "summary_preview": m.summary[:300] if m.summary else "",
            "inferred_agenda": m.inferred_agenda or "",
        }
        for m in results
    ]


@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Get a specific meeting by ID."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {
        "id": meeting.id,
        "title": meeting.title or "Untitled Meeting",
        "filename": meeting.filename,
        "duration_seconds": meeting.duration_seconds or 0,
        "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "key_points": json.loads(meeting.key_points) if meeting.key_points else [],
        "action_items": json.loads(meeting.action_items) if meeting.action_items else [],
        "speakers": json.loads(meeting.speakers) if meeting.speakers else [],
        "segments": json.loads(meeting.segments) if meeting.segments else [],
        "cleaning_used": meeting.cleaning_used,
        "insights": json.loads(meeting.insights) if meeting.insights else {},
        "role_summaries": json.loads(meeting.role_summaries) if meeting.role_summaries else {},
        "inferred_agenda": meeting.inferred_agenda,
        "roadmap": meeting.roadmap,
    }


@router.delete("/meetings/{meeting_id}")
async def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Delete a specific meeting by ID."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(meeting)
    db.commit()
    return {"message": f"Meeting {meeting_id} deleted successfully."}


@router.get("/meetings/{meeting_id}/export")
async def export_meeting(meeting_id: int, fmt: str = Query(default="markdown", description="Export format: markdown | json"), db: Session = Depends(get_db)):
    """Export a meeting's full analysis in the specified format."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    title = meeting.title or "Untitled Meeting"
    date_str = meeting.created_at.strftime("%Y-%m-%d") if meeting.created_at else "Unknown Date"
    key_points = json.loads(meeting.key_points) if meeting.key_points else []
    action_items = json.loads(meeting.action_items) if meeting.action_items else []
    insights = json.loads(meeting.insights) if meeting.insights else {}
    decisions = insights.get("decisions", [])

    if fmt == "json":
        return meeting.to_dict()

    # Markdown export
    md_lines = [
        f"# Meeting Report: {title}",
        f"**Date:** {date_str}",
        f"**Agenda:** {meeting.inferred_agenda or 'N/A'}",
        "",
        "---",
        "",
        "## Executive Summary",
        meeting.summary or "N/A",
        "",
        "## Key Points",
        *[f"- {kp}" for kp in key_points],
        "",
        "## Action Items",
        *[f"- {ai}" for ai in action_items],
        "",
        "## Key Decisions",
        *[f"- {d}" for d in decisions],
        "",
        "## Strategic Roadmap",
        meeting.roadmap or "N/A",
        "",
        "---",
        "",
        "## Full Transcript",
        meeting.transcript or "N/A",
    ]

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content="\n".join(md_lines),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="meeting_{meeting_id}.md"'}
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get aggregate statistics about all meetings."""
    meetings = db.query(Meeting).all()
    total_meetings = len(meetings)

    total_duration_seconds = sum(m.duration_seconds or 0 for m in meetings)
    total_hours = round(total_duration_seconds / 3600, 1)

    total_action_items = 0
    total_decisions = 0
    for m in meetings:
        ai_list = json.loads(m.action_items) if m.action_items else []
        total_action_items += len(ai_list)
        insights = json.loads(m.insights) if m.insights else {}
        total_decisions += len(insights.get("decisions", []))

    return {
        "total_meetings": total_meetings,
        "total_hours_processed": total_hours,
        "total_action_items": total_action_items,
        "total_decisions": total_decisions,
    }


# ─── Chat ─────────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from app.services.query_engine import query_meeting_memory


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
async def chat_with_memory(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with the meeting history memory."""
    response = query_meeting_memory(request.query, db)
    return {"response": response}
