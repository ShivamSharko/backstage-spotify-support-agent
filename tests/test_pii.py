from src.pii import redact_pii

def test_email():
    assert "[EMAIL]" in redact_pii("mail me at john.doe@example.com please")

def test_phone():
    assert "[PHONE]" in redact_pii("call me at 555-123-4567 now")

def test_url():
    assert "[URL]" in redact_pii("see https://t.co/abc123 for details")

def test_clean_text_unchanged():
    assert redact_pii("my playlist won't load") == "my playlist won't load"

