from fastapi import APIRouter, UploadFile, File, Query, WebSocket, WebSocketDisconnect
import shutil
import os
import tempfile
import json
import time
import subprocess

from app.services.transcription import transcribe_audio
from app.services.summarizer import summarize_text, summarize_structured
from app.services.cleaner import clean_audio   # <-- import

router = APIRouter()


@router.post("/transcribe/")
async def transcribe_and_summarize(
    file: UploadFile = File(...),
    language: str | None = Query(default=None, description="Force language code, e.g., 'en'"),
    model_size: str | None = Query(default=None, description="Whisper model size, e.g., tiny, base, small, medium, large"),
    enable_cleaning: bool = Query(default=True, description="Enable audio denoising if available"),
):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            shutil.copyfileobj(file.file, tmp)
            noisy_path = tmp.name

        # Define cleaned file path
        cleaned_path = noisy_path.replace(".wav", "_clean.wav")

        # Clean audio (may return noisy_path itself if cleaning fails)
        if enable_cleaning:
            used_path = clean_audio(noisy_path, cleaned_path)
        else:
            used_path = noisy_path

        # Run transcription on whichever file was actually used
        transcript = transcribe_audio(used_path, language=language, model_size=model_size)

        # Summarize transcript (structured)
        structured = summarize_structured(transcript)

        # Cleanup temp files (only if they exist)
        for path in {noisy_path, cleaned_path}:
            if os.path.exists(path):
                os.remove(path)

        return {
            "transcript": transcript,
            "summary": structured.get("summary", ""),
            "key_points": structured.get("key_points", []),
            "action_items": structured.get("action_items", []),
            "cleaning_used": enable_cleaning and (used_path != noisy_path)
        }

    except Exception as e:
        return {"error": str(e)}


@router.websocket("/ws/meeting")
async def meeting_stream(websocket: WebSocket):
    await websocket.accept()
    language = None
    model_size = None
    full_transcript = ""
    buffer = bytearray()
    last_summary_ts = 0.0
    min_chunk_size = 16000
    summary_interval = 20.0
    min_words_for_summary = 30

    try:
        while True:
            message = await websocket.receive()
            if "text" in message and message["text"] is not None:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")
                if msg_type == "start":
                    language = data.get("language")
                    model_size = data.get("model_size")
                    await websocket.send_json({"type": "started"})
                elif msg_type == "end":
                    if full_transcript.strip():
                        structured = summarize_structured(full_transcript)
                        await websocket.send_json(
                            {
                                "type": "final",
                                "transcript": full_transcript.strip(),
                                "summary": structured.get("summary", ""),
                                "key_points": structured.get("key_points", []),
                                "action_items": structured.get("action_items", []),
                            }
                        )
                    await websocket.close()
                    break

            elif "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                if not chunk:
                    continue
                buffer.extend(chunk)

                if len(buffer) < min_chunk_size:
                    continue

                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
                    tmp_in.write(buffer)
                    webm_path = tmp_in.name

                wav_path = webm_path.replace(".webm", ".wav")

                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            webm_path,
                            "-ar",
                            "16000",
                            "-ac",
                            "1",
                            wav_path,
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True,
                    )

                    text = transcribe_audio(wav_path, language=language, model_size=model_size)
                    full_transcript = (full_transcript + " " + text).strip()

                    await websocket.send_json(
                        {
                            "type": "partial_transcript",
                            "text": text,
                            "full_transcript": full_transcript,
                        }
                    )

                    now = time.time()
                    word_count = len(full_transcript.split())
                    if (
                        word_count >= min_words_for_summary
                        and now - last_summary_ts > summary_interval
                    ):
                        structured = summarize_structured(full_transcript)
                        await websocket.send_json(
                            {
                                "type": "summary_update",
                                "summary": structured.get("summary", ""),
                                "key_points": structured.get("key_points", []),
                                "action_items": structured.get("action_items", []),
                            }
                        )
                        last_summary_ts = now

                except subprocess.CalledProcessError:
                    # Ignore bad chunks that ffmpeg cannot decode; continue streaming
                    pass
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                finally:
                    if os.path.exists(webm_path):
                        os.remove(webm_path)
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                    buffer.clear()

    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
