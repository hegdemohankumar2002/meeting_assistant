from transformers import pipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to hold the pipeline
_emotion_pipeline = None

def get_emotion_pipeline():
    global _emotion_pipeline
    if _emotion_pipeline is None:
        logger.info("Loading emotion detection model...")
        try:
            # Using a popular, small, and effective model for emotion detection
            _emotion_pipeline = pipeline(
                "text-classification", 
                model="j-hartmann/emotion-english-distilroberta-base", 
                return_all_scores=False
            )
            logger.info("Emotion model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            _emotion_pipeline = None
    return _emotion_pipeline


def analyze_emotion(text: str) -> str:
    """
    Analyzes the emotion of a given text segment.
    Returns one of: anger, disgust, fear, joy, neutral, sadness, surprise
    """
    if not text or len(text.strip()) < 3:
        return "neutral"
    
    try:
        pipe = get_emotion_pipeline()
        result = pipe(text[:512])  # Limit to 512 chars for speed
        
        if isinstance(result, list) and len(result) > 0:
            top_emotion = result[0]
            return top_emotion.get('label', 'neutral')
        
        return "neutral"
    except Exception as e:
        logger.error(f"Emotion analysis failed: {e}")
        return "neutral"


def analyze_emotions_batch(texts: list[str], batch_size: int = 32) -> list[str]:
    """
    Batch process emotions for efficiency with large numbers of segments.
    
    Args:
        texts: List of text segments to analyze
        batch_size: Number of texts to process at once (default: 32)
    
    Returns:
        List of emotion labels in same order as input texts
    """
    if not texts:
        return []
    
    try:
        pipe = get_emotion_pipeline()
        emotions = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            # Truncate each text to 512 chars for speed
            batch = [text[:512] if text else "" for text in batch]
            
            # Filter out empty texts but remember their positions
            batch_with_indices = [(idx, text) for idx, text in enumerate(batch) if text.strip()]
            
            if not batch_with_indices:
                emotions.extend(["neutral"] * len(batch))
                continue
            
            indices, valid_texts = zip(*batch_with_indices) if batch_with_indices else ([], [])
            
            # Process valid texts
            if valid_texts:
                results = pipe(list(valid_texts))
                
                # Map results back to original positions
                batch_emotions = ["neutral"] * len(batch)
                for idx, result in zip(indices, results):
                    if isinstance(result, list) and len(result) > 0:
                        batch_emotions[idx] = result[0].get('label', 'neutral')
                    else:
                        batch_emotions[idx] = 'neutral'
                
                emotions.extend(batch_emotions)
            else:
                emotions.extend(["neutral"] * len(batch))
        
        return emotions
    
    except Exception as e:
        logger.error(f"Batch emotion analysis failed: {e}")
        return ["neutral"] * len(texts)
