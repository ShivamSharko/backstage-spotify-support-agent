import os
import json
import sys
import time
import re
import math
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pii import redact_pii
from src.retrieval import DenseRetriever

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ROOT = Path(__file__).resolve().parents[1]

CFG_PATH = ROOT / "configs" / "thresholds.json"
CFG = json.loads(CFG_PATH.read_text()) if CFG_PATH.exists() else None

RISK_RE = re.compile(r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b')
PROFANITY_RE = re.compile(r'\b(?:fuck|shit|bitch|kill)\w*\b')

print("Loading Dense Retriever for Risk Engine v3...")
retriever = DenseRetriever(str(ROOT / "data" / "retrieval" / "spotify_replies.csv"))

def get_intent_and_confidence(tweet):
    sys_prompt = "Classify into ONE: app_bug, account_login, billing_payment, feature_request, other. Return ONLY JSON: {\"intent\": \"...\", \"confidence\": 0.0}"
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(model=os.getenv("MODEL_NAME"), messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": tweet}], response_format={"type": "json_object"}, temperature=0.0)
            data = json.loads(resp.choices[0].message.content)
            return data.get("intent", "other"), float(data.get("confidence", 0.5))
        except Exception:
            if attempt == 0: time.sleep(1)
            else: return "other", 0.0

def get_llm_risk(tweet):
    sys_prompt = ("You are a risk assessor for customer support. Flag risk=true ONLY if the message indicates: "
                  "account compromise/hacking, fraud or unauthorized charges, legal threats, threats of violence or self-harm, "
                  "or severe abusive hostility. Do NOT flag ordinary frustration, bugs, billing questions, or sarcasm. "
                  "Return JSON only: {\"risk\": false, \"risk_type\": null} or {\"risk\": true, \"risk_type\": \"...\"}")
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(model=os.getenv("MODEL_NAME"), messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": tweet}], response_format={"type": "json_object"}, temperature=0.0)
            return bool(json.loads(resp.choices[0].message.content).get("risk", False))
        except Exception:
            if attempt == 0: time.sleep(1)
            else: return False

def keyword_flag(text):
    t = text.lower()
    if RISK_RE.search(t): return True
    if ('cancel' in t) and any(w in t for w in ["can't", "cannot", "unable", "won't"]): return True
    if PROFANITY_RE.search(t): return True
    return False

def calibrated_prob(confidence, retrieval_score):
    z = CFG['coefficients']['confidence'] * confidence + CFG['coefficients']['retrieval_score'] * retrieval_score + CFG['intercept']
    return 1 / (1 + math.exp(-z))

def risk_policy_engine(confidence, retrieval_score, text, llm_risk):
    if keyword_flag(text): return True, "High-risk keyword or dead-end (deterministic backstop)"
    if llm_risk: return True, "LLM risk classifier flag"
    if CFG:
        p = calibrated_prob(confidence, retrieval_score)
        if p >= CFG['prob_thresh']: return True, f"Calibrated risk score {p:.2f} >= {CFG['prob_thresh']}"
    else:
        if confidence < 0.7: return True, "Low LLM confidence"
        if retrieval_score < 0.4: return True, "Weak historical evidence"
    return False, "Safe to auto-handle"

def main():
    df = pd.read_csv(ROOT / "eval" / "golden_set.csv").dropna(subset=['should_escalate'])
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'
    results = []
    print(f"\nEvaluating Risk Engine v3 on {len(df)} tweets (2 LLM calls each)...")
    for i, row in df.iterrows():
        text = str(row['text'])
        safe_text = redact_pii(text)
        intent, conf = get_intent_and_confidence(safe_text)
        llm_risk = get_llm_risk(safe_text)
        ret_score = retriever.search(safe_text, top_k=1)[0]['score']
        escalate, reason = risk_policy_engine(conf, ret_score, safe_text, llm_risk)
        results.append({"text": text, "true_escalate": row['should_escalate'], "pred_escalate": escalate,
                        "intent": intent, "confidence": conf, "retrieval_score": ret_score,
                        "llm_risk": llm_risk, "reason": reason})
        time.sleep(0.2)

    res_df = pd.DataFrame(results)
    auto = ~res_df['pred_escalate']
    misses = int((auto & res_df['true_escalate']).sum())
    true_risks = int(res_df['true_escalate'].sum())
    esc = res_df['pred_escalate']
    tp = int((esc & res_df['true_escalate']).sum())

    print("\n" + "="*60)
    print("OPERATIONAL METRICS (Risk Engine v3: calibrated + LLM risk)")
    print("="*60)
    print(f"Auto-Handle Rate:           {auto.mean():.2%}")
    print(f"Volume False Auto-Handle:   {misses / int(auto.sum()):.2%}" if auto.sum() else "n/a")
    print(f"Risk Miss Rate (stricter):  {misses / true_risks:.2%}" if true_risks else "n/a")
    print(f"Risk Engine Precision:      {tp / int(esc.sum()):.2f}" if esc.sum() else "n/a")
    print(f"Risk Engine Recall:         {tp / true_risks:.2f}" if true_risks else "n/a")
    print("="*60)
    print("\nEscalation reasons:")
    print(res_df['reason'].value_counts().to_string())
    res_df.to_csv(ROOT / "eval" / "risk_engine_results.csv", index=False)

if __name__ == "__main__":
    main()
