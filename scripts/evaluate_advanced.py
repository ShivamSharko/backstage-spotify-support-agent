import os
import json
import sys
import time
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq, RateLimitError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.pii import redact_pii
from src.retrieval import DenseRetriever
from src.verifier import build_url_whitelist, verify_reply, sanitize_reply

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ROOT = Path(__file__).resolve().parents[1]

INTENT_PROMPT = (ROOT / "prompts" / "intent.md").read_text()
REPLY_PROMPT = (ROOT / "prompts" / "reply.md").read_text()
JUDGE_PROMPT = (ROOT / "prompts" / "judge.md").read_text()

print("Initializing Dense Retrieval + Grounding Verifier pipeline...")
retriever = DenseRetriever(str(ROOT / "data" / "retrieval" / "spotify_replies.csv"))

def call_with_retry(func, max_retries=5):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait_time = 60 * (i + 1)
            print(f"  ⚠️ Rate limit hit. Waiting {wait_time}s before retry {i+1}/{max_retries}...")
            time.sleep(wait_time)
    raise Exception("Max retries exceeded for Groq API.")

def get_intent(tweet):
    resp = call_with_retry(lambda: client.chat.completions.create(
        model=os.getenv("MODEL_NAME"), 
        messages=[{"role": "system", "content": INTENT_PROMPT}, {"role": "user", "content": tweet}], 
        response_format={"type": "json_object"}, temperature=0.0))
    return json.loads(resp.choices[0].message.content)["intent"]

def generate_reply(tweet, intent, evidence):
    ev_text = "\n".join([f"- [Score: {e['score']:.2f}] {e['text']}" for e in evidence])
    sys_prompt = REPLY_PROMPT + f"\nIntent: {intent}.\nRetrieved Historical Evidence:\n{ev_text}"
    resp = call_with_retry(lambda: client.chat.completions.create(
        model=os.getenv("MODEL_NAME"), 
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": f"Tweet: {tweet}\nDraft:"}], 
        temperature=0.1))
    return resp.choices[0].message.content

def judge_reply(tweet, reply):
    resp = call_with_retry(lambda: client.chat.completions.create(
        model=os.getenv("MODEL_NAME"), 
        messages=[{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": f"Tweet: {tweet}\nReply: {reply}"}], 
        response_format={"type": "json_object"}, temperature=0.0))
    return json.loads(resp.choices[0].message.content)

def main():
    replies_df = pd.read_csv(ROOT / "data" / "retrieval" / "spotify_replies.csv")
    whitelist = build_url_whitelist(replies_df['text'].fillna("").tolist())
    print(f"URL whitelist built: {len(whitelist)} entries (0 is expected since historical links are t.co)")

    golden = pd.read_csv(ROOT / "eval" / "golden_set.csv").head(20)
    results = []
    print(f"\nProcessing {len(golden)} tweets...")
    for i, row in golden.iterrows():
        original_tweet = str(row['text'])
        safe_tweet = redact_pii(original_tweet)
        intent = get_intent(safe_tweet)
        evidence = retriever.search(safe_tweet, top_k=3)
        reply = generate_reply(safe_tweet, intent, evidence)
        check = verify_reply(reply, whitelist)
        cleaned = sanitize_reply(reply, check['violations']) if check['violations'] else reply
        scores = judge_reply(original_tweet, cleaned)
        results.append({"tweet": original_tweet, "safe_tweet": safe_tweet, "intent": intent,
                        "top_retrieval_score": evidence[0]['score'], "generated_reply": cleaned,
                        "verifier_violations": len(check['violations']), "verifier_urls": "; ".join(check['violations']),
                        "judge_groundedness": scores.get("groundedness"), "judge_safety": scores.get("safety"),
                        "judge_helpfulness": scores.get("helpfulness"), "judge_critique": scores.get("critique")})
        print(f"[{i+1}/{len(golden)}] verifier_violations={len(check['violations'])}")
        time.sleep(0.5)

    out_df = pd.DataFrame(results)
    out_df.to_csv(ROOT / "eval" / "reply_eval_advanced.csv", index=False)
    print("\nADVANCED PIPELINE RESULTS (with Grounding Verifier)")
    print(f"Verifier violations caught & stripped: {int(out_df['verifier_violations'].sum())}")
    print(f"Average Groundedness: {out_df['judge_groundedness'].mean():.2f} / 5")
    print(f"Average Safety:       {out_df['judge_safety'].mean():.2f} / 5")
    print(f"Average Helpfulness:  {out_df['judge_helpfulness'].mean():.2f} / 5")

if __name__ == "__main__":
    main()
