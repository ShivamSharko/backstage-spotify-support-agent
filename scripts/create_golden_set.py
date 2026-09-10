import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLED = ROOT / "data" / "sampled"
EVAL_DIR = ROOT / "eval"

def main():
    df = pd.read_csv(SAMPLED / "spotifycares.csv")
    customers = df[df['inbound'] == True].copy()
    
    print("Sampling tweets for the Golden Evaluation Set...")
    
    # 1. Random 100 tweets (normal distribution)
    random_sample = customers.sample(100, random_state=42)
    
    # 2. High Risk 50 tweets (fraud, legal, angry, refunds)
    risk_keywords = ['hack', 'stolen', 'fraud', 'lawyer', 'sue', 'refund', 'cancel', 'scam', 'unauthorized', 'angry']
    risk_mask = customers['text'].str.lower().str.contains('|'.join(risk_keywords), na=False)
    risk_sample = customers[risk_mask & ~customers['tweet_id'].isin(random_sample['tweet_id'])].sample(min(50, risk_mask.sum()), random_state=42)
    
    # 3. Hard/Short 50 tweets (vague, short, confusing)
    short_mask = customers['text'].str.len() < 30
    short_sample = customers[short_mask & ~customers['tweet_id'].isin(random_sample['tweet_id']) & ~customers['tweet_id'].isin(risk_sample['tweet_id'])].sample(min(50, short_mask.sum()), random_state=42)
    
    # Combine them
    golden_set = pd.concat([random_sample, risk_sample, short_sample])
    
    # Add empty columns for YOU to fill out manually
    golden_set['true_intent'] = ""
    golden_set['should_escalate'] = ""
    golden_set['notes'] = ""
    
    # Keep only what we need
    golden_set = golden_set[['tweet_id', 'text', 'true_intent', 'should_escalate', 'notes']]
    
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EVAL_DIR / "golden_set_unlabelled.csv"
    golden_set.to_csv(out_path, index=False)
    
    print(f"\nSUCCESS! Created Golden Set with {len(golden_set)} tweets.")
    print(f"Saved to: {out_path}")
    print("\nBreakdown:")
    print(f" - 100 Random tweets")
    print(f" - {len(risk_sample)} High-Risk tweets")
    print(f" - {len(short_sample)} Short/Hard tweets")
    print("\nNext step: Open this CSV in Excel or Google Sheets and start labeling!")

if __name__ == "__main__":
    main()

