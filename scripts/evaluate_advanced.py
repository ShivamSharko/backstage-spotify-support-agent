import os
import json
import sys
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# Add project root to path so we can import our new src modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pii import redact_pii
from src.retrieval import DenseRetriever

# 1. Setup
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ROOT = Path(__file__).resolve().parents[1]

INTENT_PROMPT = (ROOT / "prompts" / "intent.md").read_text()
REPLY_PROMPT = (ROOT / "prompts" / "reply.md").read_text()
JUDGE_PROMPT = (ROOT / "prompts" / "judge.md").read_text()

print("Initializing 2026-Aligned Dense Retrieval Pipeline...")
retriever = DenseRetriever(str(ROOT / "data" / "retrieval" / "spotify_replies.csv"))

def get_intent(tweet):
    resp = client.chat.completions.create(model=os.getenv("MODEL_NAME"), messages=[{"role": "system", "content": INTENT_PROMPT}, {"role": "user", "content": tweet}], response_format={"type": "json_object"}, temperature=0.0)
    return json.loads(resp.choices[0].message.content)["intent"]

def generate_reply(tweet, intent, evidence):
    ev_text = "\n".join([f"- [Score: {e['score']:.2f}] {e['text']}" for e in evidence])
    sys_prompt = f"{REPLY_PROMPT}\n\nIntent: {intent}\nEvidence:\n{ev_text}"
    resp = client.chat.completions.create(model=os.getenv("MODEL_NAME"), messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": f"Tweet: {tweet}\nDraft:"}], temperature=0.1)
    return resp.choices[0].message.content

def judge_reply(tweet, reply):
    resp = client.chat.completions.create(model=os.getenv("MODEL_NAME"), messages=[{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": f"Tweet: {tweet}\nReply: {reply}"}], response_format={"type": "json_object"}, temperature=0.0)
    return json.loads(resp.choices[0].message.content)

def main():
    golden = pd.read_csv(ROOT / "eval" / "golden_set.csv").head(20) # Testing on 20 rows
    results = []
    
    print(f"\nProcessing {len(golden)} tweets with Dense Retrieval & PII Redaction...")
    for i, row in golden.iterrows():
        original_tweet = str(row['text'])
        
        # STEP 1: Redact PII
        safe_tweet = redact_pii(original_tweet)
        print(f"[{i+1}/{len(golden)}] Original: {original_tweet[:50]}...")
        if original_tweet != safe_tweet:
            print(f"      ↳ PII Redacted to: {safe_tweet[:50]}...")
        
        # STEP 2: Intent
        intent = get_intent(safe_tweet)
        
        # STEP 3: Dense Retrieval
        evidence = retriever.search(safe_tweet, top_k=3)
        top_score = evidence[0]['score']
        
        # STEP 4: Generate
        reply = generate_reply(safe_tweet, intent, evidence)
        
        # STEP 5: Judge
        scores = judge_reply(original_tweet, reply)
        
        results.append({
            "tweet": original_tweet,
            "safe_tweet": safe_tweet,
            "intent": intent,
            "top_retrieval_score": top_score,
            "generated_reply": reply,
            "judge_groundedness": scores.get("groundedness"),
            "judge_safety": scores.get("safety"),
            "judge_helpfulness": scores.get("helpfulness"),
            "judge_critique": scores.get("critique")
        })
        time.sleep(0.5)
        
    out_df = pd.DataFrame(results)
    out_path = ROOT / "eval" / "reply_eval_advanced.csv"
    out_df.to_csv(out_path, index=False)
    
    print("\n" + "="*50)
    print("ADVANCED PIPELINE RESULTS")
    print("="*50)
    print(f"Average Retrieval Score: {out_df['top_retrieval_score'].mean():.2f}")
    print(f"Average Groundedness:    {out_df['judge_groundedness'].mean():.2f} / 5")
    print(f"Average Safety:          {out_df['judge_safety'].mean():.2f} / 5")
    print(f"Average Helpfulness:     {out_df['judge_helpfulness'].mean():.2f} / 5")
    print("="*50)

if __name__ == "__main__":
    main()
