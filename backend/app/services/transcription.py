from faster_whisper import WhisperModel
import logging
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model cache
_models = {}


def get_model(model_size="small"):
    """
    Load and cache Whisper model using faster-whisper.
    4x faster than openai-whisper with same accuracy.
    
    Args:
        model_size: One of "tiny", "base", "small", "medium", "large"
    
    Returns:
        WhisperModel instance
    """
    if model_size not in _models:
        logger.info(f"Loading faster-whisper model: {model_size}")
        
        # Determine device and compute type
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Using device: {device}, compute_type: {compute_type}")
        
        try:
            _models[model_size] = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=None,  # Use default cache
                num_workers=4  # Parallel processing
            )
            logger.info(f"Model {model_size} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    return _models[model_size]


def transcribe_audio(file_path: str, language: str = None, model_size: str = "small"):
    """
    Transcribe audio file using faster-whisper.
    
    Args:
        file_path: Path to audio file
        language: Language code (e.g., "en"), None for auto-detect
        model_size: Model size to use
    
    Returns:
        dict with 'text' and 'segments' keys
    """
    logger.info(f"Transcribing {file_path} with model={model_size}, language={language}")
    
    model = get_model(model_size)
    
    # Transcribe with faster-whisper
    segments, info = model.transcribe(
        file_path,
        language=language,
        beam_size=1,
        vad_filter=True,  # Voice activity detection for better accuracy
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    # Convert generator to list and format
    all_segments = []
    full_text = []
    
    for segment in segments:
        seg_dict = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        }
        all_segments.append(seg_dict)
        full_text.append(segment.text.strip())
    
    result = {
        "text": " ".join(full_text),
        "segments": all_segments,
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration
    }
    
    logger.info(f"Transcription complete: {len(all_segments)} segments, {info.duration:.1f}s duration")
    
    return result


def transcribe_audio_chunked(file_path: str, language: str = None, model_size: str = "small", chunk_callback=None):
    """
    Transcribe audio with streaming support - yields results as they're generated.
    
    Args:
        file_path: Path to audio file
        language: Language code
        model_size: Model size
        chunk_callback: Optional callback function(segment_dict) called for each segment
    
    Yields:
        Segment dictionaries as they're transcribed
    """
    logger.info(f"Starting chunked transcription of {file_path}")
    
    model = get_model(model_size)
    
    segments, info = model.transcribe(
        file_path,
        language=language,
        beam_size=1,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    for segment in segments:
        seg_dict = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        }
        
        # Call callback if provided
        if chunk_callback:
            chunk_callback(seg_dict)
        
        # Yield for streaming
        yield seg_dict
