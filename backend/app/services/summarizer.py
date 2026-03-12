from transformers import pipeline
import logging
from typing import Optional
import os
import json
import openai
from app.config import OPENAI_API_KEY, OPENAI_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LOCAL MODEL SETUP ---
# Using a model fine-tuned on SAMSum (dialogue corpus)
MODEL_NAME = "philschmid/bart-large-cnn-samsum"

_local_summarizer = None

def get_local_summarizer():
    global _local_summarizer
    if _local_summarizer is None:
        try:
            logger.info(f"Loading local summarization model: {MODEL_NAME}")
            _local_summarizer = pipeline("summarization", model=MODEL_NAME)
            logger.info("Local summarization model loaded.")
        except Exception as e:
            logger.error(f"Failed to load {MODEL_NAME}: {e}. Falling back to default.")
            _local_summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return _local_summarizer

# --- OPENAI SETUP ---
# --- OLLAMA / LLM SETUP ---
from app.config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

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

def generate_llm_response(system_prompt: str, user_prompt: str) -> str:
    """
    Generic function to get a text response from the configured LLM.
    """
    try:
        client = get_llm_client()
        if not client:
            return "Error: AI Service Unavailable."

        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        raw_content = response.choices[0].message.content
        
        # Clean <think> tags for DeepSeek
        if "<think>" in raw_content:
            # We only want the final answer part
            parts = raw_content.split("</think>")
            if len(parts) > 1:
                return parts[-1].strip()
            return raw_content.strip() # Fallback if tag is malformed
            
        return raw_content
    except Exception as e:
        logger.error(f"LLM Generation failed: {e}")
        return f"I encountered an error while thinking: {str(e)}"

def summarize_with_llm(text: str) -> dict:
    """
    Uses Ollama (via OpenAI client compatibility) to generate a structured summary.
    Returns dict with summary, key_points, action_items.
    """
    try:
        client = get_llm_client()
        if not client:
            return None

        # UPDATED PROMPT FOR EXECUTIVE BRIEFING
        system_prompt = (
            "You are an Elite Executive Assistant. Transform this transcript into a high-impact Executive Briefing.\n"
            "## core instruction\n"
            "1. **Filter Noise**: Ignore small talk and repetition.\n"
            "2. **Extract Intelligence**: Focus on decisions, ownership, and risks.\n"
            "3. **Structure**: Use professional language.\n\n"
            "## output format (strict JSON)\n"
            "{\n"
            "  \"inferred_agenda\": \"Subject: [Topic] - [Goal]\",\n"
            "  \"summary\": \"The Bottom Line (BLUF): 3-sentence executive abstract.\",\n"
            "  \"key_points\": [\"Bullet points of critical info.\"],\n"
            "  \"action_items\": [\"[Owner] to [Verb] [Task] by [Deadline]\"],\n"
            "  \"decisions\": [\"Finalized: [Decision]\"],\n"
            "  \"risks\": [\"Risk: [Issue] -> [Mitigation]\"],\n"
            "  \"role_summaries\": {\n"
            "    \"executive\": \"Strategic implications & budget.\",\n"
            "    \"technical\": \"Architecture, code, & stack details.\"\n"
            "  }\n"
            "}"
        )

        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{text}"} # Removed truncation, relying on caller map-reduce or context window
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        content = response.choices[0].message.content
        
        # --- DeepSeek Cleanup ---
        # 1. Remove <think> blocks
        if "<think>" in content:
            content = content.split("</think>")[-1].strip()
        
        # 2. Extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()
             
        # 3. Find first '{' and last '}' to handle preamble text
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            content = content[start_idx:end_idx+1]
            
        data = json.loads(content)
        return data

    except Exception as e:
        logger.error(f"LLM Summarization failed: {e}")
        return None # Signal to fall back to local


def summarize_text(text: str, max_len: int = 150, min_len: int = 40) -> str:
    """
    Legacy wrapper for backward compatibility.
    """
    return summarize_text_local(text, max_len, min_len)


def summarize_text_local(text: str, max_len: int = 150, min_len: int = 40) -> str:
    """
    Summarize transcript using local Hugging Face model.
    """
    if not text or text.strip() == "":
        return "No transcript available."

    # Tokenizer estimation (rough): 1 word ~= 1.3 tokens
    input_len_tokens = len(text.split()) * 1.3
    if input_len_tokens < min_len:
        return text 

    try:
        adjusted_max_len = min(max_len, int(input_len_tokens * 0.8))
        adjusted_max_len = max(adjusted_max_len, min_len + 10)

        summarizer_instance = get_local_summarizer()
        summary = summarizer_instance(
            text, 
            max_length=adjusted_max_len, 
            min_length=min_len, 
            do_sample=False,
            truncation=True
        )
        return summary[0]['summary_text']
    except Exception as e:
        logger.error(f"Local summarization error: {e}")
        return text[:500] + "..."


def chunk_text_sliding_window(text: str, chunk_size: int = 400, overlap: int = 100) -> list[str]:
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunks.append(" ".join(words[i:i + chunk_size]))
        if i + chunk_size >= len(words):
            break
    return chunks

# --- MAP REDUCE LOGIC ---

def chunk_text_by_words(text: str, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """
    Chunks text by word count to stay roughly within token limits.
    Safe estimate: 1 word ~ 1.3 tokens. 3000 words ~ 4000 tokens.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]
    
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunks.append(" ".join(words[i:i + chunk_size]))
        if i + chunk_size >= len(words):
            break
    return chunks

def extract_partial_summary(text: str, client) -> dict:
    """
    Map step: Extracts key info from a chunk.
    """
    system_prompt = (
        "You are an expert transcriber. Extract the following from this meeting segment:\n"
        "1. Key discussion points (bullet points)\n"
        "2. Action items (Who, What, When)\n"
        "3. Decisions made\n"
        "Output JSON only: { \"points\": [], \"actions\": [], \"decisions\": [] }"
    )
    
    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript Segment:\n{text[:15000]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"Partial summarization failed: {e}")
        return {"points": [], "actions": [], "decisions": []}

def summarize_map_reduce(text: str) -> dict:
    """
    Map-Reduce strategy for large files.
    """
    client = get_llm_client()
    if not client:
        return None

    # Step 1: Map (Chunk & Extract)
    chunks = chunk_text_by_words(text, chunk_size=3000, overlap=300)
    logger.info(f"Map-Reduce: Split into {len(chunks)} chunks.")
    
    all_points = []
    all_actions = []
    all_decisions = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}...")
        partial = extract_partial_summary(chunk, client)
        all_points.extend(partial.get("points", []))
        all_actions.extend(partial.get("actions", []))
        all_decisions.extend(partial.get("decisions", []))

    def _to_str(item):
        """Safely convert any item (dict, list, or scalar) to a plain string."""
        if isinstance(item, dict):
            # e.g. {"who": "Alice", "what": "Fix bug", "when": "Friday"}
            parts = [f"{v}" for v in item.values() if v]
            return " — ".join(parts)
        return str(item)

    safe_points    = [_to_str(x) for x in all_points    if x]
    safe_actions   = [_to_str(x) for x in all_actions   if x]
    safe_decisions = [_to_str(x) for x in all_decisions if x]

    # Step 2: Reduce (Synthesize)
    # Create a condensed context from extracted parts
    condensed_text = (
        "Combined Notes from Meeting Segments:\n"
        f"Key Points:\n- " + "\n- ".join(safe_points    or ["None"]) + "\n\n"
        f"Action Items:\n- " + "\n- ".join(safe_actions  or ["None"]) + "\n\n"
        f"Decisions:\n- "    + "\n- ".join(safe_decisions or ["None"])
    )

    logger.info("Map-Reduce: Reducing final summary...")
    
    # Final Executive Summary Prompt
    system_prompt = (
        "You are an Executive Assistant. Transform these combined meeting notes into a final Executive Briefing.\n"
        "## Output Format (JSON)\n"
        "{\n"
        "  \"inferred_agenda\": \"Subject - Goal\",\n"
        "  \"summary\": \"3-sentence BLUF (Bottom Line Up Front)\",\n"
        "  \"key_points\": [\"Refined list of 5-7 distinct critical points\"],\n"
        "  \"action_items\": [\"[Owner] to [Verb] [Task]\"],\n"
        "  \"decisions\": [\"List of finalized decisions\"],\n"
        "  \"risks\": [\"Risk -> Mitigation\"],\n"
        "  \"role_summaries\": { \"executive\": \"...\", \"technical\": \"...\" }\n"
        "}"
    )

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": condensed_text[:25000]} # Much denser context now
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Reduce step failed: {e}")
        return None

def summarize_structured(text: str) -> dict:
    """
    Main entry point. Automatically chooses strategy based on length.
    """
    if not text or text.strip() == "":
        return {"summary": "No transcript.", "key_points": [], "action_items": [], "role_summaries": {}}

    word_count = len(text.split())
    logger.info(f"Processing transcript: {word_count} words")

    # --- STRATEGY SELECTION ---
    llm_result = None
    
    # Threshold for Map-Reduce (approx 10 pages)
    MAP_REDUCE_THRESHOLD = 4000 
    
    if word_count > MAP_REDUCE_THRESHOLD:
        logger.info(f"Large text detected ({word_count} words). Using Map-Reduce Strategy.")
        llm_result = summarize_map_reduce(text)
    else:
        logger.info(f"Short text detected ({word_count} words). Using Direct LLM Strategy.")
        llm_result = summarize_with_llm(text)

    if llm_result:
        logger.info("LLM summarization successful.")
        return {
            "summary": llm_result.get("summary", ""),
            "key_points": llm_result.get("key_points", []),
            "action_items": llm_result.get("action_items", []),
            "inferred_agenda": llm_result.get("inferred_agenda", ""), 
            "decisions": llm_result.get("decisions", []), 
            "risks": llm_result.get("risks", []), 
            "role_summaries_data": llm_result.get("role_summaries", {})
        }
    else:
        logger.warning("LLM summarization failed. Falling back to Local.")
        # Fallback to local logic (kept for safety)
        pass 

    # --- STRATEGY 2: LOCAL BART (FALLBACK) ---
    logger.info("Using Local BART sliding window...")
    chunks = chunk_text_sliding_window(text, chunk_size=500, overlap=100)
    
    partial_summaries = []
    for c in chunks:
        try:
            partial_summaries.append(summarize_text_local(c, max_len=200, min_len=50))
        except Exception:
            partial_summaries.append(c)

    combined_text = " ".join(partial_summaries)
    if len(combined_text.split()) > 600:
            final_summary = summarize_text_local(combined_text, max_len=300, min_len=100)
    else:
        final_summary = combined_text

    # Heuristic Extraction (Local Mode)
    source = text
    raw_sentences = [s.strip() for s in source.replace("\n", " ").split('.') if s.strip()]
    unique_sentences = list(set([s for s in raw_sentences if len(s.split()) > 3]))
    
    action_keywords = ["action", "todo", "follow up", "deadline", "assigned"]
    action_items = [f"{s}." for s in unique_sentences if any(k in s.lower() for k in action_keywords)][:10]
    
    summary_sentences = [s.strip() for s in final_summary.split('.') if len(s.strip()) > 20]
    key_points = [f"{s}." for s in summary_sentences if s not in action_items][:10]
    
    return {
        "summary": final_summary,
        "key_points": key_points,
        "action_items": action_items,
        "role_summaries_data": None # Local mode calculates this later
    }


def generate_role_summaries(transcript: str, insights: dict) -> dict:
    """
    Generates role-specific summaries. 
    If OpenAI already provided them (via insights check), return those.
    """
    if isinstance(insights, dict) and insights.get("role_summaries_data"):
        return insights["role_summaries_data"]

    # --- LOCAL LOGIC (as before) ---
    role_summaries = {
        "executive": "No executive summary available.",
        "technical": "No technical summary available."
    }
    
    if not transcript:
        return role_summaries

    sentences = [s.strip() for s in transcript.split('.') if s.strip()]

    # Executive
    exec_keywords = ["decid", "agre", "budget", "cost", "timeline", "deadline", "launch", "revenue"]
    exec_sentences = [s for s in sentences if any(k in s.lower() for k in exec_keywords)]
    context_pool = list(set(sentences[:5] + exec_sentences + sentences[-5:]))
    exec_text = ". ".join(context_pool)
    role_summaries["executive"] = summarize_text_local(exec_text) if len(exec_text.split()) > 50 else exec_text

    # Technical
    tech_keywords = ["api", "database", "server", "code", "bug", "deploy", "react", "python", "aws"]
    tech_sentences = [s for s in sentences if any(k in s.lower() for k in tech_keywords)]
    tech_text = ". ".join(tech_sentences)
    role_summaries["technical"] = summarize_text_local(tech_text) if len(tech_text.split()) > 50 else tech_text

    return role_summaries
