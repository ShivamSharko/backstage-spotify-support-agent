import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLED = ROOT / "data" / "sampled"
RETRIEVAL = ROOT / "data" / "retrieval"

def main():
    csv_path = SAMPLED / "spotifycares.csv"
    print(f"Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Filter for ONLY brand (outbound) tweets
    replies = df[df['inbound'] == False].copy()
    
    # Keep only the columns we need
    replies = replies[['tweet_id', 'text', 'in_response_to_tweet_id']]
    
    # Drop rows where the text is empty
    replies = replies.dropna(subset=['text'])
    
    RETRIEVAL.mkdir(parents=True, exist_ok=True)
    out_path = RETRIEVAL / "spotify_replies.csv"
    replies.to_csv(out_path, index=False)
    
    print(f"\nSUCCESS! Saved {len(replies)} brand replies to: {out_path}")
    print("\nHere are 5 examples of how Spotify replies to customers:")
    for t in replies['text'].head(5):
        print("-", t)

if __name__ == "__main__":
    main()

