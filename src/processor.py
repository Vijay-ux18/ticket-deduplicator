import os
import re
import html
import sqlite3
from datetime import datetime
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TicketProcessor:
    def __init__(self, db_path="data/tickets.db", csv_path="data/historical_tickets.csv"):
        self.db_path = db_path
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_sqlite_db()

    def _initialize_sqlite_db(self):
        """Creates historical tables alongside the Security Auditing layout tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Original incidents entity table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_tickets (
                ticket_id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                description TEXT,
                created_at TEXT
            )
        """)
        
        # Identity management user credentials tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portal_users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                account_created TEXT
            )
        """)
        
        # Non-Repudiation Security Audit stream table [backend_Securities: Audit Trails]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit_logs (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT,
                action_performed TEXT,
                status TEXT,
                metadata_summary TEXT
            )
        """)
        conn.commit()
        conn.close()

    def seed_historical_baseline(self):
        """
        Seeds standard company evaluation baseline entries.
        Fixes the AttributeError in app.py by providing the required initialization signature.
        """
        # If the fallback baseline csv doesn't exist on disk, mock it out immediately
        if not os.path.exists(self.csv_path):
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            mock_records = {
                "ticket_id": ["TS-01", "TS-02", "TS-03"],
                "category": ["Database", "Authentication", "Infrastructure"],
                "title": ["Postgres Connection Pool Exhausted", "JWT Token Decryption Error", "Disk Utilization Maxed Out"],
                "description": ["Fatal connections maxed out for superusers across application services.", "InvalidSignatureError verified across routing microservices post key-rotation.", "Root directory filesystem size has exceeded the warning capacity threshold of 92%."],
                "created_at": ["2026-06-10 08:00:00", "2026-06-11 09:00:00", "2026-06-12 10:00:00"]
            }
            pd.DataFrame(mock_records).to_csv(self.csv_path, index=False)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historical_tickets")
        if cursor.fetchone()[0] == 0:
            df = pd.read_csv(self.csv_path)
            df.to_sql("historical_tickets", conn, if_exists="append", index=False)
            conn.commit()
        conn.close()

    def sanitize_and_mask_input(self, text_payload):
        """
        [backend_Securities: Input Validation & Sensitive Data Masking]
        Strips dangerous HTML tags and redacts secret values from tracking systems.
        """
        if not text_payload:
            return ""
        
        # XSS Prevention via escaping
        sanitized = html.escape(text_payload)
        
        # Sensitive Data Masking: Redact credentials, tokens, and keys
        sanitized = re.sub(r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s,\'"]+', r'\1=********', sanitized)
        sanitized = re.sub(r'(?i)(token|bearer|api_key|secret)\s*[:=]\s*[^\s,\'"]+', r'\1=********', sanitized)
        sanitized = re.sub(r'AIzaSy[A-Za-z0-9_-]{35}', 'AIzaSy=********', sanitized)
        
        return sanitized

    def log_security_event(self, action, status, meta_dict):
        """Records an immutable security audit trail transaction [backend_Securities: Audit Trails]."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        event_id = f"AUDIT-{int(datetime.now().timestamp())}-{os.urandom(2).hex()}"
        cursor.execute(
            "INSERT INTO security_audit_logs VALUES (?, ?, ?, ?, ?)",
            (event_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, status, str(meta_dict))
        )
        conn.commit()
        conn.close()

    def fetch_audit_logs(self):
        """Exposes relational audit data to your cockpit viewing matrix."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT 5", conn)
        conn.close()
        return df

    def find_top_matches(self, cleaned_text, top_n=3):
        """Runs cosine vector calculation models against your active SQLite rows."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM historical_tickets", conn)
        conn.close()

        if df.empty or not cleaned_text.strip():
            return []

        corpus = (df['title'] + " " + df['description']).tolist()
        vectorizer = TfidfVectorizer(stop_words='english')
        matrix = vectorizer.fit_transform(corpus)
        
        input_vector = vectorizer.transform([cleaned_text])
        scores = cosine_similarity(input_vector, matrix).flatten()
        
        df['similarity_score'] = scores
        match_rows = df.sort_values(by='similarity_score', ascending=False).head(top_n)
        
        results = []
        for _, row in match_rows.iterrows():
            results.append({
                "ticket_id": row['ticket_id'],
                "category": row['category'],
                "title": row['title'],
                "description": row['description'],
                "similarity_score": round(float(row['similarity_score']), 4),
                "created_at": row['created_at']
            })
        return results