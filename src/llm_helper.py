import os
import json
from google import genai
from google.genai import types

class LLMDeduplicatorHelper:
    def __init__(self):
        # Securely capture API keys from the host Ubuntu shell environment
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            # New 2026 standard Client initialization pattern
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = 'gemini-1.5-flash'
        else:
            self.client = None

    def _read_prompt_template(self):
        """Safely extracts system prompt layouts from disk."""
        prompt_path = "prompts.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                return f.read()
        return ""

    def verify_duplicate_status(self, incoming_text, historical_matches):
        """
        Structures historical records, prompts the new LLM Client layer, 
        and validates that the returned output is a valid JSON schema.
        """
        # Fallback mechanism to ensure the app functions cleanly offline or if credentials aren't set
        if not self.api_key or not self.client:
            return self._generate_local_fallback(historical_matches)

        context_str = ""
        for match in historical_matches:
            context_str += f"\n- Ticket ID: {match['ticket_id']}\n"
            context_str += f"  Title: {match['title']}\n"
            context_str += f"  Description: {match['description']}\n"
            context_str += f"  Math Score: {match['similarity_score']}\n"

        full_prompt = self._read_prompt_template()
        if not full_prompt:
            return self._generate_local_fallback(historical_matches)

        formatted_prompt = full_prompt.format(
            incoming_ticket_text=incoming_text,
            historical_db_context=context_str
        )

        try:
            # Modern SDK structured output generation call
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception:
            return self._generate_local_fallback(historical_matches)

    def _generate_local_fallback(self, historical_matches):
        """Ensures a functional end-to-end flow even during upstream API outages."""
        if not historical_matches:
            return {
                "is_duplicate": False,
                "confidence_percentage": 0,
                "target_duplicate_id": None,
                "reasoning": "No historical database context found to execute comparison operations.",
                "recommended_action": "Route ticket to standard L1 queue."
            }
        
        best_match = historical_matches[0]
        is_dup = best_match['similarity_score'] > 0.65
        return {
            "is_duplicate": bool(is_dup),
            "confidence_percentage": int(best_match['similarity_score'] * 100),
            "target_duplicate_id": best_match['ticket_id'] if is_dup else None,
            "reasoning": f"Local vector engine isolated maximum overlap with {best_match['ticket_id']} (Math Similarity Score: {best_match['similarity_score']}).",
            "recommended_action": f"Link to {best_match['ticket_id']} and mark as a candidate duplicate." if is_dup else "Keep open and assign to an L2 engineer."
        }
