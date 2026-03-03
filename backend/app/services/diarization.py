import os
import torch
from pyannote.audio import Pipeline
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

_pipeline = None

def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        if not HF_TOKEN:
            raise ValueError("HF_TOKEN is missing in .env file. Required for pyannote.audio.")
        
        try:
            _pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=HF_TOKEN
            )
            
            if torch.cuda.is_available():
                _pipeline.to(torch.device("cuda"))
        except Exception as e:
            print(f"[DIARIZATION] Failed to load pipeline: {e}")
            raise e
            
    return _pipeline

def diarize_audio(file_path: str):
    """
    Diarize the given audio file and return a list of segments.
    Returns:
        list of dict: [{"start": float, "end": float, "speaker": str}, ...]
    """
    try:
        pipeline = _get_pipeline()
        diarization = pipeline(file_path)

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        return segments
    except Exception as e:
        print(f"[DIARIZATION] Error processing file: {e}")
        return []
