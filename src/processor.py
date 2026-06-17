import os
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TicketProcessor:
    def __init__(self, db_path="data/tickets.db", csv_path="data/historical_tickets.csv"):
        self.db_path = db_path
        self.csv_path = csv_path
        # Enforce secure directory handling on Ubuntu 26.04
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_sqlite_db()

    def _initialize_sqlite_db(self):
        """Creates a zero-setup local SQLite DB and auto-seeds it if empty."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build core relational schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_tickets (
                ticket_id TEXT PRIMARY KEY,
                category TEXT,
                title TEXT,
                description TEXT,
                created_at TEXT
            )
        """)
        conn.commit()
        
        # Seed records only if the target database table is empty
        cursor.execute("SELECT COUNT(*) FROM historical_tickets")
        if cursor.fetchone()[0] == 0:
            if os.path.exists(self.csv_path):
                df = pd.read_csv(self.csv_path)
                df.to_sql("historical_tickets", conn, if_exists="append", index=False)
                conn.commit()
        conn.close()

    def fetch_all_historical_tickets(self):
        """Extracts complete database records into a DataFrame snapshot."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM historical_tickets", conn)
        conn.close()
        return df

    def find_top_matches(self, new_ticket_text, top_n=3):
        """
        Tokenizes text data and computes cosine similarity matrices.
        Returns the top 3 mathematically closest historical records.
        """
        df = self.fetch_all_historical_tickets()
        if df.empty:
            return []

        # Combine title and description to build rich textual context tokens
        historical_corpus = (df['title'] + " " + df['description']).tolist()
        
        # Build frequency vectors using scikit-learn
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(historical_corpus)
        
        # Vectorize new incoming incident text parameters
        new_vector = vectorizer.transform([new_ticket_text])
        
        # Compute exact mathematical cosine similarity matrices
        similarity_scores = cosine_similarity(new_vector, tfidf_matrix).flatten()
        
        # Map similarity percentages back to data elements
        df['similarity_score'] = similarity_scores
        
        # Filter, sort descending, and isolate the closest candidates
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
