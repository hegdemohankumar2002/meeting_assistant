from fastapi import APIRouter, UploadFile, File, Query, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
import json
from app.services.transcription import transcribe_audio, transcribe_audio_chunked
from app.services.summarizer import summarize_text, summarize_structured, generate_role_summaries
from app.services.cleaner import clean_audio
from app.services.diarization import diarize_audio
from app.services.emotion import analyze_emotion, analyze_emotions_batch
from app.services.intelligence import extract_insights
from app.services.roadmap_generator import generate_roadmap
from app.database import get_db
from app.models.db_models import Meeting
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file and return server path for streaming processing.
    """
    try:
        # Save to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        return {"file_path": tmp_path, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def align_segments(whisper_segments, diarization_segments):
    """
    Assign speakers to Whisper segments based on time overlap with diarization segments.
    Also performs batch emotion analysis for efficiency.
    """
    aligned_segments = []
    speakers_map = {} # id -> {id, label, color}
    
    # Helper to get/create speaker obj
    def get_speaker(spk_label):
        if spk_label not in speakers_map:
            speakers_map[spk_label] = {
                "id": spk_label,
                "label": spk_label.replace("_", " ").title(),
                "color": "#888888"
            }
        return speakers_map[spk_label]

    # First pass: align speakers
    for seg in whisper_segments:
        start = seg["start"]
        end = seg["end"]
        text = seg["text"]
        
        # Find overlapping diarization segment
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
            "emotion": None  # Will be filled in batch
        })
    
    # Second pass: batch emotion analysis
    # texts = [seg["text"] for seg in aligned_segments]
    # emotions = analyze_emotions_batch(texts, batch_size=32)
    
    # for seg, emotion in zip(aligned_segments, emotions):
    #     seg["emotion"] = emotion
    pass
        
    return list(speakers_map.values()), aligned_segments


@router.post("/transcribe/")
async def transcribe_and_summarize(
    file: UploadFile = File(...),
    language: str | None = Query(default=None, description="Force language code, e.g., 'en'"),
    model_size: str | None = Query(default=None, description="Whisper model size, e.g., tiny, base, small, medium, large"),
    enable_cleaning: bool = Query(default=True, description="Enable audio denoising if available"),
    db: Session = Depends(get_db),
):
    print("DEBUG: Endpoint /transcribe/ hit")
    
    # Log file size for monitoring
    file_size_mb = 0
    try:
        file.file.seek(0, 2)
        file_size_bytes = file.file.tell()
        file.file.seek(0)
        file_size_mb = file_size_bytes / (1024 * 1024)
        print(f"INFO: Processing file: {file.filename} ({file_size_mb:.2f} MB)")
        
        if file_size_mb > 10:
            print(f"WARNING: Large file detected ({file_size_mb:.2f} MB). Processing may take several minutes.")
    except Exception as e:
        print(f"WARNING: Could not determine file size: {e}")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        print(f"DEBUG: Saved to temp file: {tmp_path}")

        # Optional cleaning
        cleaning_used = False
        if enable_cleaning:
            cleaned_path = clean_audio(tmp_path)
            if cleaned_path != tmp_path:
                print("DEBUG: Audio cleaning applied")
                cleaning_used = True
                os.remove(tmp_path)
                tmp_path = cleaned_path

        # Transcription with faster-whisper
        print("DEBUG: Starting transcription...")
        transcription_result = transcribe_audio(
            tmp_path,
            language=language,
            model_size=model_size or "small"
        )
        transcript_text = transcription_result["text"]
        whisper_segments = transcription_result["segments"]
        print(f"DEBUG: Transcription done. Text length: {len(transcript_text)}")

        # Diarization
        print("DEBUG: Starting diarization...")
        diarization_segments = diarize_audio(tmp_path)
        print(f"DEBUG: Diarization done. Found {len(set(d['speaker'] for d in diarization_segments))} speakers")

        # Align segments with speakers and emotions
        print("DEBUG: Aligning segments with speakers and analyzing emotions...")
        speakers, aligned_segments = align_segments(whisper_segments, diarization_segments)
        print(f"DEBUG: Alignment done. {len(aligned_segments)} segments aligned")

        # Summarization
        print("DEBUG: Starting summarization...")
        structured_summary = summarize_structured(transcript_text)
        print("DEBUG: Summarization done")

        # Extract insights
        print("DEBUG: Extracting insights...")
        insights = extract_insights(transcript_text)
        
        # Merge insights from summarizer (decisions, risks) into intelligence insights
        if structured_summary.get("decisions"):
            insights["decisions"] = structured_summary["decisions"] + insights.get("decisions", [])
        if structured_summary.get("risks"):
            insights["risks"] = structured_summary.get("risks", [])
            
        print(f"DEBUG: Insights extracted: {len(insights.get('decisions', []))} decisions, {len(insights.get('agreements', []))} agreements, {len(insights.get('conflicts', []))} conflicts")

        # Generate role-specific summaries
        print("DEBUG: Generating role-specific summaries...")
        role_summaries = generate_role_summaries(transcript_text, structured_summary)
        print("DEBUG: Role summaries generated")

        # Generate Roadmap
        print("DEBUG: Generating roadmap...")
        roadmap_md = generate_roadmap(structured_summary)
        print("DEBUG: Roadmap generated")

        # Save to database
        print("DEBUG: Saving to database...")
        meeting = Meeting(
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
        print(f"DEBUG: Saved to DB with ID: {meeting.id}")

        # Cleanup
        os.remove(tmp_path)

        return {
            "id": meeting.id,
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
            "roadmap": roadmap_md
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
    Sends progress updates as processing happens.
    """
    await websocket.accept()
    
    try:
        # Receive initial data with file path
        data = await websocket.receive_json()
        file_path = data.get('file_path')
        language = data.get('language')
        model_size = data.get('model_size', 'small')
        enable_cleaning = data.get('enable_cleaning', True)
        
        if not file_path or not os.path.exists(file_path):
            await websocket.send_json({"error": "Invalid file path"})
            return
        
        # Stage 1: Transcription with streaming
        await websocket.send_json({
            "stage": "transcription",
            "status": "started",
            "message": "Starting transcription..."
        })
        
        all_segments = []
        full_text = []
        
        for segment in transcribe_audio_chunked(file_path, language, model_size):
            all_segments.append(segment)
            full_text.append(segment["text"])
            
            # Send each segment as it's transcribed
            await websocket.send_json({
                "stage": "transcription",
                "status": "progress",
                "segment": segment,
                "partial_text": " ".join(full_text)
            })
        
        transcript_text = " ".join(full_text)
        
        await websocket.send_json({
            "stage": "transcription",
            "status": "done",
            "text": transcript_text,
            "segment_count": len(all_segments)
        })
        
        # Stage 2: Diarization
        await websocket.send_json({
            "stage": "diarization",
            "status": "started",
            "message": "Identifying speakers..."
        })
        
        diarization_segments = diarize_audio(file_path)
        speakers, aligned_segments = align_segments(all_segments, diarization_segments)
        
        await websocket.send_json({
            "stage": "diarization",
            "status": "done",
            "speakers": speakers,
            "segments": aligned_segments
        })
        
        # Stage 3: Analysis (Summary, Insights, Emotions)
        await websocket.send_json({
            "stage": "analysis",
            "status": "started",
            "message": "Analyzing meeting content..."
        })
        
        # Summarization
        structured_summary = summarize_structured(transcript_text)
        
        await websocket.send_json({
            "stage": "analysis",
            "status": "progress",
            "type": "summary",
            "data": structured_summary
        })
        
        # Insights
        insights = extract_insights(transcript_text)
        
        await websocket.send_json({
            "stage": "analysis",
            "status": "progress",
            "type": "insights",
            "data": insights
        })
        
        # Role summaries
        role_summaries = generate_role_summaries(transcript_text, structured_summary)
        
        await websocket.send_json({
            "stage": "analysis",
            "status": "done",
            "type": "role_summaries",
            "data": role_summaries
        })
        
        # Save to database
        meeting = Meeting(
            transcript=transcript_text,
            summary=structured_summary["summary"],
            key_points=json.dumps(structured_summary["key_points"]),
            action_items=json.dumps(structured_summary["action_items"]),
            speakers=json.dumps(speakers),
            segments=json.dumps(aligned_segments),
            cleaning_used=enable_cleaning,
            insights=json.dumps(insights),
            role_summaries=json.dumps(role_summaries)
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        
        # Send completion
        await websocket.send_json({
            "stage": "complete",
            "meeting_id": meeting.id,
            "message": "Processing complete!"
        })
        
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


@router.get("/meetings/")
async def get_meetings(db: Session = Depends(get_db)):
    """Get all meetings"""
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "created_at": m.created_at.isoformat(),
            "transcript_preview": m.transcript[:200] if m.transcript else "",
            "summary_preview": m.summary[:200] if m.summary else ""
        }
        for m in meetings
    ]


@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Get a specific meeting by ID"""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return {
        "id": meeting.id,
        "created_at": meeting.created_at.isoformat(),
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
        "roadmap": meeting.roadmap
    }


from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str

from app.services.query_engine import query_meeting_memory

@router.post("/chat")
async def chat_with_memory(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with the meeting history memory.
    """
    response = query_meeting_memory(request.query, db)
    return {"response": response}
