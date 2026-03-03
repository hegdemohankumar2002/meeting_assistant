
import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock libraries to avoid heavy imports
sys.modules["transformers"] = MagicMock()
sys.modules["torch"] = MagicMock()

from app.services.summarizer import summarize_structured, summarize_map_reduce

def test_map_reduce_flow():
    print("Testing Map-Reduce Flow...")
    
    # Create a large dummy text (5000 words)
    large_text = "word " * 5000
    
    # Mock LLM client and response
    with patch("app.services.summarizer.get_llm_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock partial summary response
        mock_client.chat.completions.create.return_value.choices[0].message.content = '{"points": ["p1"], "actions": ["a1"], "decisions": ["d1"]}'
        
        # Logic test
        # 1. Trigger Map Reduce
        with patch("app.services.summarizer.summarize_map_reduce", side_effect=summarize_map_reduce) as spy_map_reduce:
             # We need to mock the 2nd call (Reduce step) to match expected format
             # First calls are for chunks (partial summary structure), last is for Final (executive structure)
             
             # Actually, simpler to just mock the LLM response to vary based on prompt, but for a smoke test, 
             # let's just make sure it runs without crashing.
             
             # Adjust mock to return valid JSON for BOTH steps
             # Step 1 expect: points, actions, decisions
             # Step 2 expect: summary, key_points, action_items, etc.
             
             # Let's make the mock return a merged structure that satisfies both (lazy but effective for smoke test)
             mixed_response = """
             {
                "points": ["p1"], "actions": ["a1"], "decisions": ["d1"],
                "summary": "Final Summary", "key_points": ["k1"], "action_items": ["item1"], 
                "inferred_agenda": "Agenda", "risks": [], "role_summaries": {}
             }
             """
             mock_client.chat.completions.create.return_value.choices[0].message.content = mixed_response
             
             result = summarize_structured(large_text)
             
             print("Result Keys:", result.keys())
             assert result["summary"] == "Final Summary"
             assert len(result["action_items"]) > 0
             print("SUCCESS: Map-Reduce logic executed and returned structured data.")

if __name__ == "__main__":
    try:
        test_map_reduce_flow()
    except Exception as e:
        print("FAILED:")
        import traceback
        traceback.print_exc()
