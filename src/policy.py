import re

RISK_RE = re.compile(r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue\w*|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b')
PROFANITY_RE = re.compile(r'\b(?:fuck|shit|bitch|kill)\w*\b')
DEAD_END_WORDS = ["can't", "cannot", "unable", "won't"]

def keyword_flag(text: str) -> bool:
    t = str(text).lower()
    if RISK_RE.search(t):
        return True
    if ('cancel' in t) and any(w in t for w in DEAD_END_WORDS):
        return True
    if PROFANITY_RE.search(t):
        return True
    return False

def predict_escalation(tweet: str, intent: str) -> bool:
    return keyword_flag(tweet)

