from transformers import pipeline
import logging
import re
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to hold the pipeline
# --- OLLAMA / LLM SETUP ---
from app.config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
import openai

def get_llm_client():
    try:
        client = openai.OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize LLM client: {e}")
        return None

def extract_insights(transcript: str) -> dict:
    """
    Extracts decisions, agreements, and conflicts from the transcript using Ollama.
    Returns a dict: {
        "decisions": [list of sentences],
        "agreements": [list of sentences],
        "conflicts": [list of sentences]
    }
    """
    insights = {
        "decisions": [],
        "agreements": [],
        "conflicts": []
    }

    if not transcript or not transcript.strip():
        return insights

    client = get_llm_client()
    if not client:
        return insights

    system_prompt = (
        "You are an expert meeting analyst. Analyze the provided transcript segments. "
        "Identify and extract key insights in three categories: Decisions, Agreements, and Conflicts. "
        "Return the result in strict JSON format:\n"
        "{\n"
        "  \"decisions\": [\"List of clear decisions made, e.g., 'We will launch on Friday.'\"],\n"
        "  \"agreements\": [\"List of points where participants reached a consensus.\"],\n"
        "  \"conflicts\": [\"List of disagreements, concerns raised, or opposing views.\"]\n"
        "}"
        "\nOnly include significant points. If none found for a category, return an empty list."
    )

    try:
        logger.info(f"Extracting insights using {OLLAMA_MODEL}...")
        
        # Split long transcripts to fit context if needed, but for now we try a large chunk
        # or rely on the model's context window.
        
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript[:15000]}"} 
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        
        insights["decisions"] = data.get("decisions", [])
        insights["agreements"] = data.get("agreements", [])
        insights["conflicts"] = data.get("conflicts", [])
        
        logger.info(f"Extracted {len(insights['decisions'])} decisions, {len(insights['agreements'])} agreements, {len(insights['conflicts'])} conflicts")

    except Exception as e:
        logger.error(f"LLM Intelligence extraction failed: {e}")
        # Could fall back to simple keyword search if needed, but for now returning empty is safer than crashing

    return insights
