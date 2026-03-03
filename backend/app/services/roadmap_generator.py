from app.config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
import logging
import json
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def generate_roadmap(insights: dict) -> str:
    """
    Generates a strategic implementation roadmap based on the inferred agenda and extracted insights.
    Returns a Markdown string.
    """
    if not insights or not insights.get("inferred_agenda"):
        return "No agenda inferred. Cannot generate roadmap."

    client = get_llm_client()
    if not client:
        return "LLM Client unavailable."

    agenda = insights.get("inferred_agenda")
    decisions = insights.get("decisions", [])
    action_items = insights.get("action_items", [])
    risks = insights.get("risks", [])
    key_points = insights.get("key_points", [])

    prompt_context = f"""
    Agenda: {agenda}
    Decisions: {json.dumps(decisions)}
    Action Items: {json.dumps(action_items)}
    Key Points: {json.dumps(key_points)}
    Risks: {json.dumps(risks)}
    """

    system_prompt = (
        "You are a Project Manager. Based on the provided meeting insights, generate a clear, strategic Implementation Roadmap in Markdown format.\n"
        "Structure the roadmap as follows:\n"
        "1. **Mission Statement**: Rephrase the agenda as a clear goal.\n"
        "2. **Strategic Milestones**: Break down the implementation into 3-5 key phases.\n"
        "3. **Task Breakdown**: Assign the action items to the relevant phases.\n"
        "4. **Risk Mitigation**: addressing the identified risks.\n\n"
        "Keep it professional, concise, and actionable."
    )

    try:
        logger.info(f"Generating roadmap for agenda: {agenda}")
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Meeting Context:\n{prompt_context}"}
            ],
            temperature=0.3
        )
        
        roadmap_md = response.choices[0].message.content
        return roadmap_md

    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}")
        return "Failed to generate roadmap."
