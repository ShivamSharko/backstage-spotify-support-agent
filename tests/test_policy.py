from src.policy import keyword_flag, predict_escalation

def test_issue_not_flagged():
    assert not keyword_flag("Haha, no issues. Love the time capsule")
    assert not keyword_flag("I have an issue with my playlist")

def test_true_risk_flagged():
    assert keyword_flag("my account was hacked yesterday")
    assert keyword_flag("unauthorized charges on my card")
    assert keyword_flag("I will sue you people")
    assert keyword_flag("this is fraud, report it")

def test_sues_plural_flagged():
    assert keyword_flag("he sues the company")
    assert keyword_flag("they are suing spotify")

def test_dead_end_flagged():
    assert keyword_flag("I can't cancel my subscription anywhere")

def test_intent_gate():
    assert predict_escalation("my account was hacked", "account_login")
    assert not predict_escalation("no issues here", "app_bug")

