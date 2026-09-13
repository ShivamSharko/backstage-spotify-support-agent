import re

RISK_RE = re.compile(r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue\w*|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b')
PROFANITY_RE = re.compile(r'\b(?:fuck|shit|bitch|kill)\w*\b')
DEAD_END_RE = re.compile(r"\b(?:can't|cannot|cant|unable|won't|wont)\b")

def keyword_flag(text: str) -> bool:
    t = str(text).lower()
    if RISK_RE.search(t):
        return True
    if ("cancel" in t) and DEAD_END_RE.search(t):
        return True
    if PROFANITY_RE.search(t):
        return True
    return False

def predict_escalation(tweet: str, intent: str) -> bool:
    has_risk = keyword_flag(tweet)
    if intent == "account_login" and has_risk:
        return True
    return has_risk

