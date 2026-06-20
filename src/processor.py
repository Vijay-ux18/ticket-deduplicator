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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Original incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_tickets (
                ticket_id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                description TEXT,
                created_at TEXT
            )
        """)
        
        # Upgraded Feature: Security Audit Log Table [backend_Securities: Audit Trails]
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
        
        # Seed records if empty
        cursor.execute("SELECT COUNT(*) FROM historical_tickets")
        if cursor.fetchone()[0] == 0 and os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            df.to_sql("historical_tickets", conn, if_exists="append", index=False)
            conn.commit()
        conn.close()

    def sanitize_and_mask_input(self, text_payload):
        """
        [backend_Securities: Input Validation & Sensitive Data Masking]
        Strips HTML injection vectors and redacts passwords/API keys from logs.
        """
        if not text_payload:
            return ""
        
        # XSS Prevention 
        sanitized = html.escape(text_payload)
        
        # Data Masking: Never log passwords, tokens, or keys 
        sanitized = re.sub(r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s,\'"]+', r'\1=********', sanitized)
        sanitized = re.sub(r'(?i)(token|bearer|api_key|secret)\s*[:=]\s*[^\s,\'"]+', r'\1=********', sanitized)
        sanitized = re.sub(r'AIzaSy[A-Za-z0-9_-]{35}', 'AIzaSy=********', sanitized)
        
        return sanitized

    def log_security_event(self, action, status, meta):
        """Records an immutable security audit event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        event_id = f"AUDIT-{int(datetime.now().timestamp())}"
        cursor.execute(
            "INSERT INTO security_audit_logs VALUES (?, ?, ?, ?, ?)",
            (event_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, status, str(meta))
        )
        conn.commit()
        conn.close()

    def fetch_audit_logs(self):
        """Exposes audit data for your dashboard visibility grid."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT 5", conn)
        conn.close()
        return df

    def fetch_all_historical_tickets(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM historical_tickets", conn)
        conn.close()
        return df

    def find_top_matches(self, new_ticket_text, top_n=3):
        df = self.fetch_all_historical_tickets()
        if df.empty or not new_ticket_text.strip():
            return []
        historical_corpus = (df['title'] + " " + df['description']).tolist()
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(historical_corpus)
        new_vector = vectorizer.transform([new_ticket_text])
        similarity_scores = cosine_similarity(new_vector, tfidf_matrix).flatten()
        df['similarity_score'] = similarity_scores
        top_df = df.sort_values(by='similarity_score', ascending=False).head(top_n)
        
        results = []
        for _, row in top_df.iterrows():
            results.append({
                "ticket_id": row['ticket_id'],
                "category": row['category'],
                "title": row['title'],
                "description": row['description'],
                "similarity_score": round(float(row['similarity_score']), 4),
                "created_at": row['created_at']
            })
        return results