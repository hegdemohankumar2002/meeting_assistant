from transformers import pipeline

# Load Hugging Face summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

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

def summarize_structured(text: str) -> dict:
    if not text or text.strip() == "":
        return {"summary": "No transcript available to summarize.", "key_points": [], "action_items": []}

    # For long transcripts, summarize in chunks first
    chunks = []
    current = []
    words = text.split()
    total = 0
    for w in words:
        current.append(w)
        total += 1
        if total >= 350:
            chunks.append(" ".join(current))
            current = []
            total = 0
    if current:
        chunks.append(" ".join(current))

    partial_summaries = []
    for c in chunks:
        s = summarizer(c, max_length=140, min_length=40, do_sample=False)
        partial_summaries.append(s[0]["summary_text"])

    combined = " ".join(partial_summaries) if len(partial_summaries) > 1 else partial_summaries[0]

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
