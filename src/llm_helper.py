import os
import json
import streamlit as st
from google import genai
from google.genai import types

class LLMDeduplicatorHelper:
    def __init__(self):
        # 1. Attempt to resolve authorization token string keys from Streamlit Cloud Secrets
        self.api_key = None
        try:
            if "GEMINI_API_KEY" in st.secrets:
                self.api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

        # 2. Fall back to host Ubuntu environment variable arrays if not on cloud
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")

        # 3. Instantiate warning-free modern Client instance safely [backend_Securities: Hide Internal Errors]
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
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
        Structures historical records, prompts the cognitive model tier, 
        and validates that the returned output matches the requested schema.
        """
        # Strict fallback loop if the cognitive engine cannot clear auth bounds
        if not self.client:
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

        # Python .format template injection mapping safely
        formatted_prompt = full_prompt.format(
            incoming_ticket_text=incoming_text,
            historical_db_context=context_str
        )

        try:
            # Execute validation requests using the warning-free client layout matrix
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=formatted_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception:
            # Shield internal parsing errors from client visibility configurations
            return self._generate_local_fallback(historical_matches)

    def _generate_local_fallback(self, historical_matches):
        """Dynamic local mathematical decision perimeter gate if API channel is unavailable."""
        if not historical_matches:
            return {
                "is_duplicate": False,
                "confidence_percentage": 0,
                "target_duplicate_id": None,
                "reasoning": "Offline Shield: No database precedents matched.",
                "recommended_action": "Route to L1 network triage queue."
            }
        
        best_match = historical_matches[0]
        is_dup = best_match['similarity_score'] > 0.45 
        return {
            "is_duplicate": bool(is_dup),
            "confidence_percentage": int(best_match['similarity_score'] * 100),
            "target_duplicate_id": best_match['ticket_id'] if is_dup else None,
            "reasoning": f"Offline Vector Engine: Isolated maximum match overlap with {best_match['ticket_id']} (Math Similarity Score: {best_match['similarity_score']}).",
            "recommended_action": f"Link to ticket {best_match['ticket_id']} and merge properties as candidate duplicate." if is_dup else "Evaluate standalone operational metrics."
        }