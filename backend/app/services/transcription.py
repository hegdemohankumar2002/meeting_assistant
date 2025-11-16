import os
from pathlib import Path
import whisper
import torch

_models = {}

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _get_model(name: str):
    name = name or os.getenv("WHISPER_MODEL", "medium")
    key = f"{name}:{DEVICE}"
    if key not in _models:
        _models[key] = whisper.load_model(name, device=DEVICE)
    return _models[key]

def transcribe_audio(file_path: str, language: str | None = None, model_size: str | None = None) -> str:
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    model = _get_model(model_size)
    opts = dict(
        language=language,
        temperature=0.0,
        beam_size=5,
        best_of=5,
        condition_on_previous_text=False,
        fp16=False,
    )
    result = model.transcribe(file_path, **{k: v for k, v in opts.items() if v is not None})
    return result.get("text", "")
