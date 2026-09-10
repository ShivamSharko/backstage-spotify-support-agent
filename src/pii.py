import re

def redact_pii(text: str) -> str:
    """Redacts emails, phone numbers, and URLs to protect user privacy before sending to LLM."""
    if not isinstance(text, str): return text
    # Redact emails
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]', text)
    # Redact phone numbers (basic patterns)
    text = re.sub(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    # Redact URLs
    text = re.sub(r'http\S+|www\.\S+', '[URL]', text)
    return text

