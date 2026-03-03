from transformers import pipeline
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Hugging Face summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# LangChain imports (lazy loaded)
_langchain_available = False
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain.chains.summarize import load_summarize_chain
    from langchain_openai import ChatOpenAI
    from langchain_core.documents import Document
    from app.config import OPENAI_API_KEY, OPENAI_MODEL, USE_HIERARCHICAL_SUMMARIZATION_THRESHOLD
    from app.services.chunking import get_chunker
    _langchain_available = True
    logger.info("LangChain loaded successfully for hierarchical summarization")
except ImportError as e:
    logger.warning(f"LangChain not available: {e}. Will use BART for all summarization.")

# Initialize LangChain components (lazy)
_llm = None
_text_splitter = None

def summarize_text(text: str, max_len: int = 120, min_len: int = 30) -> str:
    """
    Summarize transcript using Hugging Face model.
    """
    if not text or text.strip() == "":
        return "No transcript available to summarize."

    summary = summarizer(
        text, 
        max_length=max_len, 
        min_length=min_len, 
        do_sample=False
    )
    return summary[0]['summary_text']

def summarize_long_text_hierarchical(text: str) -> str:
    """
    Summarize very long text using LangChain's map-reduce approach.
    This is more effective for transcripts > 5000 words.
    """
    global _llm, _text_splitter
    
    if not _langchain_available:
        logger.warning("LangChain not available, falling back to BART chunking")
        return summarize_text(text[:3000])  # Fallback to BART with truncation
    
    try:
        # Initialize LLM if not already done
        if _llm is None:
            _llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=0,
                openai_api_key=OPENAI_API_KEY
            )
        
        # Initialize text splitter if not already done
        if _text_splitter is None:
            _text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=3000,  # Characters, not tokens
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        
        # Split text into chunks
        chunks = _text_splitter.split_text(text)
        docs = [Document(page_content=chunk) for chunk in chunks]
        
        logger.info(f"Hierarchical summarization: {len(docs)} chunks created")
        
        # Use map_reduce chain for long documents
        chain = load_summarize_chain(
            _llm, 
            chain_type="map_reduce",
            verbose=False
        )
        
        result = chain.run(docs)
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error in hierarchical summarization: {e}")
        # Fallback to BART
        return summarize_text(text[:3000])


def summarize_structured(text: str) -> dict:
    if not text or text.strip() == "":
        return {"summary": "No transcript available to summarize.", "key_points": [], "action_items": []}

    word_count = len(text.split())
    logger.info(f"Summarizing transcript with {word_count} words")
    
    # Decide whether to use hierarchical summarization
    use_hierarchical = (
        _langchain_available and 
        word_count > USE_HIERARCHICAL_SUMMARIZATION_THRESHOLD
    )
    
    if use_hierarchical:
        logger.info("Using hierarchical summarization (LangChain)")
        # Use LangChain for very long transcripts
        combined = summarize_long_text_hierarchical(text)
    else:
        logger.info("Using BART chunked summarization")
        # For long transcripts, summarize in chunks first (BART approach)
        chunks = []
        current = []
        words = text.split()
        total = 0
        chunk_size = 350  # Keep smaller chunks for BART
        
        for w in words:
            current.append(w)
            total += 1
            if total >= chunk_size:
                chunks.append(" ".join(current))
                current = []
                total = 0
        if current:
            chunks.append(" ".join(current))

        partial_summaries = []
        for c in chunks:
            try:
                # Adjust min_length based on chunk length to avoid errors
                chunk_len = len(c.split())
                min_l = min(40, chunk_len // 2)
                max_l = min(140, chunk_len)
                
                if chunk_len < 20:
                    # Too short to summarize, just keep it
                    partial_summaries.append(c)
                else:
                    s = summarizer(c, max_length=max_l, min_length=min_l, do_sample=False)
                    partial_summaries.append(s[0]["summary_text"])
            except Exception as e:
                logger.error(f"Error summarizing chunk: {e}")
                # Include original chunk if summarization fails
                partial_summaries.append(c)

        combined = " ".join(partial_summaries) if len(partial_summaries) > 0 else text[:500]

    # Split into sentences, normalize whitespace, and deduplicate while preserving order
    raw_sentences = [s.strip() for s in combined.replace("\n", " ").split('.') if s.strip()]
    seen = set()
    sentences = []
    for s in raw_sentences:
        low = s.lower()
        if low not in seen:
            seen.add(low)
            sentences.append(s)

    # Heuristically detect action-like sentences (things to do / follow-up)
    action_keywords = [
        "action", "todo", "to do", "follow up", "follow-up",
        "should", "need to", "must", "have to", "please", "ask",
        "finish", "complete", "decide", "decisions", "plan", "next step",
    ]

    action_points = []
    other_points = []
    for s in sentences:
        text_l = s.lower()
        if any(kw in text_l for kw in action_keywords):
            action_points.append(f"{s}.")
        else:
            other_points.append(f"{s}.")

    # Summary: first 2–3 distinct sentences give the overall picture
    summary_core = sentences[:3] if sentences else []
    summary_text = " ".join(summary_core) + ("." if summary_core else "")

    # Number of points scales with transcript length (but keep an upper bound)
    total_sentences = len(sentences)
    # Rough heuristic: allow more points for longer discussions, up to 20
    max_points = min(max(5, total_sentences), 20)

    # Action items: all detected actions, but clipped by max_points
    action_items = action_points[:max_points]

    # Key points: remaining context sentences that are NOT already
    # part of the summary_core or action_items, up to remaining budget
    summary_set = {s.lower() for s in summary_core}
    action_set = {a.strip().lower() for a in action_items}

    remaining_slots = max_points - len(action_items)
    key_points = []
    if remaining_slots > 0:
        for s in sentences:
            candidate = f"{s}."
            low = s.lower()
            if low in summary_set:
                continue
            if candidate.strip().lower() in action_set:
                continue
            key_points.append(candidate)
            if len(key_points) >= remaining_slots:
                break

    return {
        "summary": summary_text or combined,
        "key_points": key_points,
        "action_items": action_items,
    }
def generate_role_summaries(transcript: str, insights: dict) -> dict:
    """
    Generates role-specific summaries (Executive, Technical) based on transcript and insights.
    """
    role_summaries = {
        "executive": "No executive summary available.",
        "technical": "No technical summary available."
    }
    
    if not transcript:
        return role_summaries

    # --- Executive Summary ---
    # Focus: Decisions, Agreements, and high-level context (start/end of meeting)
    # Strategy: Concatenate decisions/agreements + first 5 sentences + last 5 sentences
    
    sentences = [s.strip() for s in transcript.split('.') if s.strip()]
    intro = ". ".join(sentences[:5])
    outro = ". ".join(sentences[-5:]) if len(sentences) > 10 else ""
    
    decisions_text = ". ".join(insights.get("decisions", []))
    agreements_text = ". ".join(insights.get("agreements", []))
    
    exec_context = f"{intro}. {decisions_text}. {agreements_text}. {outro}."
    
    # Summarize the filtered context
    # If context is too short, just use it as is
    if len(exec_context.split()) > 50:
        role_summaries["executive"] = summarize_text(exec_context)
    else:
        role_summaries["executive"] = exec_context

    # --- Technical Summary ---
    # Focus: Technical terms, bugs, implementation
    tech_keywords = [
        "api", "database", "server", "client", "frontend", "backend", "code", "bug", "error", 
        "deploy", "git", "react", "python", "sql", "json", "endpoint", "function", "class",
        "variable", "loop", "async", "await", "docker", "cloud", "aws", "azure", "testing"
    ]
    
    tech_sentences = []
    for sent in sentences:
        if any(k in sent.lower() for k in tech_keywords):
            tech_sentences.append(sent)
            
    if tech_sentences:
        tech_context = ". ".join(tech_sentences)
        if len(tech_context.split()) > 50:
            role_summaries["technical"] = summarize_text(tech_context)
        else:
            role_summaries["technical"] = tech_context
    else:
        role_summaries["technical"] = "No technical content detected in this meeting."

    return role_summaries
