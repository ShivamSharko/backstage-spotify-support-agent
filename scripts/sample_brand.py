import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SAMPLED = ROOT / "data" / "sampled"

COLS = ["tweet_id", "author_id", "inbound", "created_at", "text",
        "response_tweet_id", "in_response_to_tweet_id"]


def find_main_csv():
    csvs = [p for p in RAW.rglob("*.csv")]
    if not csvs:
        sys.exit("ERROR: No .csv file found inside data/raw.")
    return max(csvs, key=lambda p: p.stat().st_size)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/sample_brand.py BrandName")
    brand = sys.argv[1]
    mention = "@" + brand.lower()

    main_csv = find_main_csv()
    print("Scanning for brand:", brand)

    brand_ids = set()
    for chunk in pd.read_csv(main_csv, chunksize=200_000, usecols=COLS):
        ids = chunk.loc[chunk["author_id"] == brand, "tweet_id"]
        brand_ids.update(ids.tolist())
    print("Brand tweets found:", len(brand_ids))

    kept = []
    for chunk in pd.read_csv(main_csv, chunksize=200_000, usecols=COLS):
        text = chunk["text"].fillna("").str.lower()
        mask = (
            (chunk["author_id"] == brand)
            | (chunk["in_response_to_tweet_id"].isin(brand_ids))
            | (chunk["response_tweet_id"].isin(brand_ids))
            | (text.str.contains(mention, regex=False))
        )
        if mask.any():
            kept.append(chunk[mask])

    if not kept:
        sys.exit("ERROR: No rows found for this brand.")

    df = pd.concat(kept, ignore_index=True)
    df["inbound"] = df["inbound"].astype(bool)

    SAMPLED.mkdir(parents=True, exist_ok=True)
    out_path = SAMPLED / f"{brand.lower()}.csv"
    df.to_csv(out_path, index=False)

    print("\nSaved subset to:", out_path)
    print("Total rows:", len(df))
    print("Customer (inbound) rows:", int(df["inbound"].sum()))
    print("Brand (outbound) rows:", int((~df["inbound"]).sum()))
    print("\nExample customer messages:")
    for t in df.loc[df["inbound"], "text"].head(10):
        print("-", t)


if __name__ == "__main__":
    main()

