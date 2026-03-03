from sqlalchemy.orm import Session
from app.models.db_models import Meeting
from app.services.summarizer import generate_llm_response
import json

def query_meeting_memory(query: str, db: Session) -> str:
    """
    Search past meetings for relevance to the query and generate an answer.
    Currently uses basic keyword search and LLM synthesis.
    """
    # 1. Fetch all meetings (optimized: could use vector search later)
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).limit(10).all()
    
    if not meetings:
        return "I don't have any meeting records yet."
    
    # 2. Prepare Context (Naive approach: concate summaries)
    # For a real scalable system, we'd use embeddings. 
    # Here, we fit as much as we can into the context window.
    context_parts = []
    
    for m in meetings:
        # Check if relevant (naive check)
        # In a real app, use vector DB. Here, we just dump recent summaries.
        date_str = m.created_at.strftime("%Y-%m-%d") if m.created_at else "Unknown Date"
        
        # Try to parse insights for better context
        decisions = []
        try:
            # Try to parse insights for better context
            insights = json.loads(m.insights) if m.insights else {}
            decisions_raw = insights.get("decisions", [])
            # Ensure decisions is a list of strings
            if isinstance(decisions_raw, list):
                decisions = [str(d) for d in decisions_raw]
            else:
                decisions = []
        except Exception:
            decisions = []
            
        context_parts.append(f"""
        --- Meeting ID {m.id} ({date_str}) ---
        Agenda: {m.inferred_agenda or 'N/A'}
        Summary: {m.summary or 'N/A'}
        Decisions: {', '.join(decisions)}
        """)
    
    context_text = "\n".join(context_parts)
    
    # 3. Ask LLM
    system_prompt = (
        "You are an intelligent AI Meeting Assistant and long-term memory for a team. "
        "Your goal is to be helpful, conversational, and context-aware.\n\n"
        "## Guidelines:\n"
        "1. **Conversational**: If the user greets you (e.g., 'hi', 'hello') or asks a general question, respond naturally and politely. Do NOT look for this in the meeting history.\n"
        "2. **Fact-Based**: If the user asks about specific topics, decisions, or past meetings, answer ONLY based on the provided 'Meeting History'.\n"
        "3. **Citations**: When referencing facts from history, mention the Meeting Date majorly.\n"
        "4. **Honesty**: If a specific fact is seemingly not in the history, say 'I don't see that in the records' rather than making it up."
    )
    
    user_prompt = f"""
    Meeting History:
    {context_text}
    
    User Query: {query}
    """
    
    return generate_llm_response(system_prompt, user_prompt)
