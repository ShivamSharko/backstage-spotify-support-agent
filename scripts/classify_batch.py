import os
import json
import time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# 1. Load secrets and connect to Groq
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

system_prompt = """You are an AI assistant that classifies customer support tweets for Spotify.
Classify the tweet into exactly ONE of these intents:
- app_bug: The app is crashing, freezing, music won't play, or a feature is broken.
- account_login: Trouble logging in, resetting password, or hacked account.
- billing_payment: Issues with Premium subscription, charges, or refunds.
- feature_request: Asking how to do something or requesting a new feature.
- other: Praise, spam, or unrelated to the above.

Return ONLY valid JSON with these exact keys:
{
  "intent": "the chosen intent",
  "confidence": "a number between 0.0 and 1.0",
  "reason": "a brief 1-sentence explanation"
}"""

def main():
    # 2. Load our sampled Spotify data
    csv_path = Path(__file__).resolve().parents[1] / "data" / "sampled" / "spotifycares.csv"
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Filter for ONLY customer (inbound) tweets and take the first 100
    customers = df[df['inbound'] == True].head(100)
    print(f"Found {len(customers)} customer tweets to classify.\n")
    
    results = []
    
    # 3. Loop through the tweets
    for index, row in customers.iterrows():
        tweet = str(row['text'])
        tweet_id = row['tweet_id']
        print(f"[{index+1}/100] Analyzing: {tweet[:60]}...")
        
        try:
            response = client.chat.completions.create(
                model=os.getenv("MODEL_NAME"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": tweet}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            parsed = json.loads(response.choices[0].message.content)
            
            results.append({
                "tweet_id": tweet_id,
                "text": tweet,
                "intent": parsed.get("intent", "error"),
                "confidence": parsed.get("confidence", "0.0"),
                "reason": parsed.get("reason", "")
            })
            
            # Small sleep so we don't hit Groq's free tier limits
            time.sleep(0.2) 
            
        except Exception as e:
            print(f"  ERROR on tweet {tweet_id}: {e}")
            results.append({
                "tweet_id": tweet_id,
                "text": tweet,
                "intent": "error",
                "confidence": "0.0",
                "reason": str(e)
            })

    # 4. Save to a new CSV file
    out_path = Path(__file__).resolve().parents[1] / "data" / "sampled" / "classified_100.csv"
    out_df = pd.DataFrame(results)
    out_df.to_csv(out_path, index=False)
    
    print(f"\nSUCCESS! Saved results to: {out_path}")
    print("\nSummary of intents found:")
    print(out_df['intent'].value_counts())

if __name__ == "__main__":
    main()

