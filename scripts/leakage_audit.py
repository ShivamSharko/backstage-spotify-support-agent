import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    sampled = pd.read_csv(ROOT / "data" / "sampled" / "spotifycares.csv")
    golden = pd.read_csv(ROOT / "eval" / "golden_set.csv")

    brand_replies = set(sampled[~sampled["inbound"].astype(bool)]["tweet_id"])
    print(f"Total brand replies in dataset (RAG corpus): {len(brand_replies)}")

    golden_ids = set(golden["tweet_id"])
    golden_in_sampled = sampled[sampled["tweet_id"].isin(golden_ids)]

    has_response = golden_in_sampled["response_tweet_id"].notna()
    leaked_responses = golden_in_sampled[has_response]["response_tweet_id"].isin(brand_replies)

    leaked_count = leaked_responses.sum()
    total_with_responses = has_response.sum()

    print(f"Golden tweets with a brand response in the dataset: {total_with_responses}")
    print(f"Golden tweets whose response is in the RAG corpus: {leaked_count}")
    
    if leaked_count > 0:
        print("\nDISCLOSURE: The golden set is in-distribution for the retrieval corpus.")
        print("Add this to REPORT.md Section 4: 'The golden set tweets have their historical brand replies present in the RAG corpus, meaning retrieval-groundedness metrics are in-distribution and optimistic compared to a strictly held-out test set.'")
    else:
        print("\nNo direct-thread leakage detected.")

if __name__ == "__main__":
    main()
