# 🤖 AI Usage Note

This documentation is a mandatory deliverable for the AI Prototype Challenge, capturing the exact collaboration engineering loop between the development team and the AI coding agent during the 3-day sprint.

## 1. What AI Helped With
* **Algorithmic Text Vectorization Pipeline:** The AI generated the core data pre-processing mathematics inside `src/processor.py`, specifically using `scikit-learn`'s `TfidfVectorizer` and `cosine_similarity` matrix calculations to isolate the top 3 matching historical support records.
* **Streamlit Single-Screen Layout Architecture:** The AI cleanly structured the multi-column visual presentation layout in `app.py`, allowing side-by-side presentation of data injection buttons, input text areas, database grids, and markdown report exporters on a single screen without multi-page UI bloat.
* **Relational Package Initialization:** The AI provided standard package configurations by mapping `__init__.py` files across package subdirectories, ensuring safe absolute module paths for Python under Ubuntu 26.04 LTS.

## 2. What AI Got Wrong & How We Fixed It
* **The Error — Markdown Wrap in JSON Outputs:** Initially, when instructed to generate structured triage evaluations, the Gemini API returned its text payload enclosed inside markdown backticks (e.g., ` ```json ... ``` `). This caused a catastrophic `json.decoder.JSONDecodeError` crash inside the Python backend core parser loop.
* **The Resolution — API Guardrail Enforcement:** We addressed this failure in `src/llm_helper.py` by configuring Gemini's native structured compilation rules, passing `generation_config={"response_mime_type": "application/json"}` directly to the model instance. This completely forced a clean, un-wrapped JSON dictionary token stream.
* **The Error — Version Architecture Drift:** The AI originally suggested static, outdated versions for `requirements.txt`.
* **The Resolution — Version Upgrades:** We updated the dependencies to enforce the cutting-edge version requirements (`pandas>=3.0.0`, `scikit-learn>=1.5.0`) to match our corporate environment stack on Ubuntu 26.04 LTS.

## 3. Best Performing Prompts Used
The single most successful prompt template utilized to anchor deterministic AI response architectures inside `prompts.md` was:

```markdown
You are an advanced IT Production Support AI Agent operating within an automated ticket triage loop.

Incoming Support Ticket:
"""
{incoming_ticket_text}
"""

Top 3 Mathematically Similar Historical Tickets Found in DB:
{historical_db_context}

Task:
Compare the incoming ticket against the historical matches. Determine if this issue is an exact or near-exact functional duplicate that should be linked and closed to prevent engineering alert fatigue.

You must return your response in a strict, valid JSON format using these exact keys:
{{
  "is_duplicate": true/false,
  "confidence_percentage": 0-100,
  "target_duplicate_id": "TS-XX or null",
  "reasoning": "A concise, 2-sentence technical comparison explaining why it is or isn't a duplicate.",
  "recommended_action": "Link to ticket TS-XX and close as duplicate OR Route to L2 engineer for isolation."
}}
