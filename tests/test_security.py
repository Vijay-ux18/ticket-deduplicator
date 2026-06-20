import pytest
from src.processor import TicketProcessor

def test_security_input_sanitization_and_masking():
    proc = TicketProcessor(db_path="data/test_upgrade.db")
    dirty_input = "<script>bad()</script> admin_password=SecretKey123"
    
    clean_output = proc.sanitize_and_mask_input(dirty_input)
    
    # Verify XSS and Masking blocks are operational
    assert "<script>" not in clean_output
    assert "&lt;script&gt;" in clean_output
    assert "SecretKey123" not in clean_output
    assert "admin_password=********" in clean_output