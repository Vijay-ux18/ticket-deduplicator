import os
import json
import google.generativeai as genai
import streamlit as st

class LLMDeduplicatorHelper:
    def __init__(self):
        # 1. Attempt to grab from Streamlit Cloud Native Secrets management platform
        self.api_key = None
        try:
            if "GEMINI_API_KEY" in st.secrets:
                self.api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass

        # 2. Fall back to native host Ubuntu system environment variable string arrays if not on cloud
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")

        # 3. Configure the generative model engine instance securely
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def _read_prompt_template(self):
        """Safely extracts system prompt layouts from disk."""
        prompt_path = "prompts.md"
        if os.path.exists(prompt_path):
            with open(prompt_path, "r") as f:
                return f.read()
        return ""

    def verify_duplicate_status(self, incoming_text, historical_matches):
        """
        Structures historical records, prompts the LLM layer, 
        and validates that the returned output is a valid JSON schema.
        """
        # If no API key was successfully initialized, fall back to mathematical scoring metrics
        if not self.api_key or not self.model:
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
            # Force clean JSON response token strings out of the model engine configurations
            response = self.model.generate_content(
                formatted_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception:
            return self._generate_local_fallback(historical_matches)

    def _generate_local_fallback(self, historical_matches):
        """Fallback mechanism to ensure the application remains testable when keys are absent."""
        if not historical_matches:
            return {
                "is_duplicate": False,
                "confidence_percentage": 0,
                "target_duplicate_id": None,
                "reasoning": "Offline Mode: No database records matched.",
                "recommended_action": "Route to L1 triage queue."
            }
        
        best_match = historical_matches[0]
        # Use an organic structural threshold check for local math
        is_dup = best_match['similarity_score'] > 0.45 
        return {
            "is_duplicate": bool(is_dup),
            "confidence_percentage": int(best_match['similarity_score'] * 100),
            "target_duplicate_id": best_match['ticket_id'] if is_dup else None,
            "reasoning": f"Offline Vector Engine: Isolated maximum match overlap with {best_match['ticket_id']} (Math Similarity Score: {best_match['similarity_score']}).",
            "recommended_action": f"Link to ticket {best_match['ticket_id']} and merge properties as candidate duplicate." if is_dup else "Evaluate standalone operational metrics."
        }
