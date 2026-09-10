import os
import json
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from sklearn.metrics import classification_report, f1_score, accuracy_score, precision_score, recall_score

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

system_prompt = """You are an AI assistant that classifies customer support tweets for Spotify.
Classify the tweet into exactly ONE of these intents: app_bug, account_login, billing_payment, feature_request, other.
Return ONLY valid JSON: {"intent": "..."}"""

def get_intent(tweet):
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME"),
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": tweet}],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        parsed = json.loads(response.choices[0].message.content)
        return parsed.get("intent", "error")
    except Exception as e:
        print(f"  Error calling AI: {e}")
        return "error"

def predict_escalation(tweet, intent):
    # Simple rule-based escalation (our baseline logic)
    text_lower = str(tweet).lower()
    # Rule 1: Security / Hacking
    if intent == 'account_login' and any(k in text_lower for k in ['hack', 'stolen', 'phish', 'unauthorized', 'compromised']):
        return True
    # Rule 2: Legal / Fraud
    if any(k in text_lower for k in ['lawyer', 'sue', 'legal', 'fraud', 'scam']):
        return True
    # Rule 3: Extreme frustration/profanity
    if any(k in text_lower for k in ['fuck', 'shit', 'bitch']):
        return True
    return False

def main():
    eval_path = Path(__file__).resolve().parents[1] / "eval" / "golden_set.csv"
    df = pd.read_csv(eval_path)
    
    # Drop any rows that don't have true labels just in case
    df = df.dropna(subset=['true_intent', 'should_escalate'])
    
    # Convert string "True"/"False" to actual booleans
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'
    
    print(f"Evaluating {len(df)} tweets against the Golden Set...")
    
    true_intents = []
    pred_intents = []
    true_escalations = []
    pred_escalations = []
    
    for i, row in df.iterrows():
        tweet = str(row['text'])
        true_int = row['true_intent']
        true_esc = row['should_escalate']
        
        print(f"[{i+1}/{len(df)}] Classifying...")
        pred_int = get_intent(tweet)
        pred_esc = predict_escalation(tweet, pred_int)
        
        true_intents.append(true_int)
        pred_intents.append(pred_int)
        true_escalations.append(true_esc)
        pred_escalations.append(pred_esc)
        
        time.sleep(0.2)
        
    print("\n" + "="*50)
    print("INTENT CLASSIFICATION RESULTS")
    print("="*50)
    print(f"Accuracy: {accuracy_score(true_intents, pred_intents):.2f}")
    print(f"Macro F1-Score: {f1_score(true_intents, pred_intents, average='macro', zero_division=0):.2f}")
    print("\nDetailed Report:")
    print(classification_report(true_intents, pred_intents, zero_division=0))
    
    print("="*50)
    print("ESCALATION RESULTS")
    print("="*50)
    print(f"Escalation Precision: {precision_score(true_escalations, pred_escalations, zero_division=0):.2f}")
    print(f"Escalation Recall: {recall_score(true_escalations, pred_escalations, zero_division=0):.2f}")
    print("\nDetailed Report:")
    print(classification_report(true_escalations, pred_escalations, target_names=['Auto-Handle (False)', 'Escalate (True)'], zero_division=0))

if __name__ == "__main__":
    main()

