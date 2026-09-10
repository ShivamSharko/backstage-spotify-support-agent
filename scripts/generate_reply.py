import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Setup connections
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
ROOT = Path(__file__).resolve().parents[1]

# 2. Load historical replies and build search index
print("Loading search index...")
df = pd.read_csv(ROOT / "data" / "retrieval" / "spotify_replies.csv")
df['text'] = df['text'].fillna("")
vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
tfidf_matrix = vectorizer.fit_transform(df['text'])
print("Ready!\n")

def get_intent(tweet):
    system_prompt = """Classify the tweet into ONE intent: app_bug, account_login, billing_payment, feature_request, other.
    Return ONLY JSON: {"intent": "..."}"""
    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME"),
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": tweet}],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    return json.loads(response.choices[0].message.content)["intent"]

def get_evidence(tweet):
    query_vec = vectorizer.transform([tweet])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-3:][::-1]
    return [df.iloc[i]['text'] for i in top_indices]

def generate_reply(tweet, intent, evidence):
    evidence_text = "\n".join([f"- {e}" for e in evidence])
    
    system_prompt = f"""You are an AI drafting a customer support reply for Spotify.
    
    Customer Intent: {intent}
    Historical examples of how we reply:
    {evidence_text}
    
    Rules:
    1. Be polite, concise, and professional.
    2. Ground your reply in the historical examples. Do not invent fake policies, fake refund timelines, or fake features.
    3. If the evidence is not enough to solve the issue, ask the customer to DM us their email address for privacy.
    4. Do not use emojis."""

    response = client.chat.completions.create(
        model=os.getenv("MODEL_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Customer tweet: {tweet}\n\nDraft the reply:"}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content

def main():
    # Test with a real-world style tweet
    tweet = "@SpotifyCares my premium subscription was charged twice this month, I need a refund please!"
    
    print(f"CUSTOMER TWEET: {tweet}\n")
    
    # Step A: Intent
    intent = get_intent(tweet)
    print(f"1. DETECTED INTENT: {intent}\n")
    
    # Step B: Evidence
    evidence = get_evidence(tweet)
    print("2. HISTORICAL EVIDENCE FOUND:")
    for i, e in enumerate(evidence, 1):
        print(f"   [{i}] {e}")
    print()
    
    # Step C: Generation
    print("3. DRAFTING REPLY...")
    reply = generate_reply(tweet, intent, evidence)
    print("\n--- AI GENERATED DRAFT ---")
    print(reply)
    print("--------------------------\n")

if __name__ == "__main__":
    main()

