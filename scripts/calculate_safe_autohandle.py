import os
import json
import sys
import time
import re
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

print("Loading Dense Retriever for Risk Engine...")
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

def risk_policy_engine(intent, confidence, retrieval_score, text):
    if confidence < 0.7: return True, "Low LLM confidence"
    if retrieval_score < 0.4: return True, "Weak historical evidence"
    
    text_lower = text.lower()
    risk_pattern = r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b'
    has_risk = bool(re.search(risk_pattern, text_lower))
    has_dead_end = ('cancel' in text_lower) and any(w in text_lower for w in ["can't", "cannot", "unable", "won't"])
    has_profanity = bool(re.search(r'\b(?:fuck|shit|bitch|kill)\w*\b', text_lower))
    
    if has_risk or has_dead_end or has_profanity:
        return True, "High-risk keyword or dead-end detected"
    
    return False, "Safe to auto-handle"

def main():
    df = pd.read_csv(ROOT / "eval" / "golden_set.csv")
    df = df.dropna(subset=['should_escalate'])
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'
    
    results = []
    print(f"\nEvaluating Risk Engine on {len(df)} tweets...")
    
    for i, row in df.iterrows():
        text = str(row['text'])
        safe_text = redact_pii(text)
        intent, conf = get_intent_and_confidence(safe_text)
        evidence = retriever.search(safe_text, top_k=1)
        ret_score = evidence[0]['score']
        escalate, reason = risk_policy_engine(intent, conf, ret_score, safe_text)
        
        results.append({
            "text": text, "true_escalate": row['should_escalate'], "pred_escalate": escalate,
            "intent": intent, "confidence": conf, "retrieval_score": ret_score, "reason": reason
        })
        time.sleep(0.2)
        
    res_df = pd.DataFrame(results)
    auto_handle_count = (~res_df['pred_escalate']).sum()
    total = len(res_df)
    auto_handle_rate = auto_handle_count / total
    
    false_auto_handles = ((res_df['true_escalate'] == True) & (res_df['pred_escalate'] == False)).sum()
    false_auto_handle_rate = false_auto_handles / auto_handle_count if auto_handle_count > 0 else 0
    
    true_risks = res_df['true_escalate'].sum()
    risk_miss_rate = false_auto_handles / true_risks if true_risks > 0 else 0
    
    print("\n" + "="*60)
    print("OPERATIONAL METRICS (Risk & Confidence Engine)")
    print("="*60)
    print(f"Auto-Handle Rate:             {auto_handle_rate:.2%}")
    print(f"Volume False Auto-Handle:     {false_auto_handle_rate:.2%}")
    print(f"Risk Miss Rate (Stricter):    {risk_miss_rate:.2%}")
    print("="*60)
    
    res_df.to_csv(ROOT / "eval" / "risk_engine_results.csv", index=False)

if __name__ == "__main__":
    main()
