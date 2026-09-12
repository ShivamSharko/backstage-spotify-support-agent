import os
import json
import time
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ROOT = Path(__file__).resolve().parents[1]

INTENT_PROMPT = (ROOT / "prompts" / "intent.md").read_text()

def call_with_retry(func, max_retries=5):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "rate limit" in str(e).lower():
                wait_time = 60 * (i + 1)
                print(f"  ⚠️ Rate limit hit. Waiting {wait_time}s before retry {i+1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                if i == 0: time.sleep(1)
                else: raise
    raise Exception("Max retries exceeded for Groq API.")

def get_intent(tweet):
    return call_with_retry(lambda: _get_intent_impl(tweet))
    
def _get_intent_impl(tweet):
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[{"role": "system", "content": INTENT_PROMPT}, {"role": "user", "content": tweet}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        parsed = json.loads(response.choices[0].message.content)
        return parsed.get("intent", "error"), float(parsed.get("confidence", 0.5))
    except Exception:
        return "error", 0.0

def predict_escalation(tweet, intent):
    text_lower = str(tweet).lower()
    # FIX: \w* allows suffixes (hack\w* matches hacked/hacking) while \b prevents "issue"
    risk_pattern = r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b'
    has_risk = bool(re.search(risk_pattern, text_lower))
    has_dead_end = ('cancel' in text_lower) and any(w in text_lower for w in ["can't", "cannot", "unable", "won't"])
    has_profanity = bool(re.search(r'\b(?:fuck|shit|bitch|kill)\w*\b', text_lower))
    
    if intent == 'account_login' and has_risk: return True
    if has_risk or has_dead_end or has_profanity: return True
    return False

def main():
    eval_path = ROOT / "eval" / "golden_set.csv"
    df = pd.read_csv(eval_path).dropna(subset=['true_intent', 'should_escalate'])
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'
    
    pred_intents, pred_escs, confs = [], [], []
    for i, row in df.iterrows():
        tweet = str(row['text'])
        print(f"[{i+1}/{len(df)}] Classifying...")
        p_int, conf = get_intent(tweet)
        p_esc = predict_escalation(tweet, p_int)
        pred_intents.append(p_int)
        pred_escs.append(p_esc)
        confs.append(conf)
        time.sleep(0.1)
        
    df['pred_intent'] = pred_intents
    df['pred_escalate'] = pred_escs
    df['confidence'] = confs
    df.to_csv(ROOT / "eval" / "intent_predictions.csv", index=False)
    
    print("\nINTENT METRICS:")
    print(f"Accuracy: {accuracy_score(df['true_intent'], df['pred_intent']):.2%}")
    print(f"Macro F1: {f1_score(df['true_intent'], df['pred_intent'], average='macro', zero_division=0):.2f}")
    print("\nESCALATION METRICS (Rule-Based Baseline):")
    print(f"Precision: {precision_score(df['should_escalate'], df['pred_escalate'], zero_division=0):.2f}")
    print(f"Recall: {recall_score(df['should_escalate'], df['pred_escalate'], zero_division=0):.2f}")

if __name__ == "__main__":
    main()
