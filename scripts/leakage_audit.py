import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    sampled = pd.read_csv(ROOT / "data" / "sampled" / "spotifycares.csv")
    golden = pd.read_csv(ROOT / "eval" / "golden_set.csv")
    print("Sampled columns:", sampled.columns.tolist())

    inbound = sampled["inbound"].astype(bool)
    corpus_ids = set(sampled[~inbound]["tweet_id"])
    print(f"Retrieval corpus replies: {len(corpus_ids)}")

    if "response_id" not in sampled.columns:
        print("ERROR: 'response_id' column missing from sampled csv; cannot link golden tweets to their thread replies.")
        return

    gm = sampled[sampled["tweet_id"].isin(set(golden["tweet_id"]))]
    leaked = gm[gm["response_id"].isin(corpus_ids)]
    print(f"Golden tweets: {len(golden)}")
    print(f"Golden tweets whose OWN thread's brand reply is inside the retrieval corpus: {len(leaked)}")
    if len(leaked):
        print("Leaked tweet_ids:", leaked["tweet_id"].tolist())
        print("Disclose in REPORT section 4: groundedness/helpfulness on those rows is optimistic.")
    else:
        print("No direct-thread leakage detected.")

if __name__ == "__main__":
    main()
