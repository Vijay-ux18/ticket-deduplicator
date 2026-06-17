import os
import pytest
import sqlite3
import pandas as pd
from src.processor import TicketProcessor

@pytest.fixture
def setup_test_environment(tmp_path):
    """Generates temporary sandbox folders to isolate local integration tests."""
    test_db = os.path.join(tmp_path, "test_tickets.db")
    test_csv = os.path.join(tmp_path, "test_tickets.csv")
    
    mock_data = {
        "ticket_id": ["TS-99", "TS-100"],
        "category": ["Database", "Network"],
        "title": ["Postgres Out of Memory Exception", "VPC Connection Timeout Failure"],
        "description": ["Fatal OOM crash on primary write cluster node", "Connection dropped between microservices"],
        "created_at": ["2026-06-15 00:00:00", "2026-06-15 01:00:00"]
    }
    df = pd.DataFrame(mock_data)
    df.to_csv(test_csv, index=False)
    
    processor = TicketProcessor(db_path=test_db, csv_path=test_csv)
    yield processor

def test_database_initialization_and_seeding(setup_test_environment):
    """Validates that the serverless SQLite layer populates from file seeds perfectly."""
    processor = setup_test_environment
    df = processor.fetch_all_historical_tickets()
    
    assert len(df) == 2
    assert "ticket_id" in df.columns
    assert df.iloc[0]['ticket_id'] == "TS-99"

def test_vector_similarity_scoring_precision(setup_test_environment):
    """Validates that the core vector processor isolates the correct similar row."""
    processor = setup_test_environment
    
    # Input text explicitly designed to target the database memory crash row
    input_text = "System warning: Database server node crashed with a critical Out Of Memory memory fault"
    
    matches = processor.find_top_matches(input_text, top_n=1)
    
    assert len(matches) == 1
    assert matches[0]['ticket_id'] == "TS-99"
    assert matches[0]['similarity_score'] > 0.2  # Confirms valid mathematical vector tracking
