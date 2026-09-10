import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def find_main_csv():
    csvs = [p for p in RAW.rglob("*.csv")]
    if not csvs:
        sys.exit("ERROR: No .csv file found inside data/raw (or its subfolders).")
    return max(csvs, key=lambda p: p.stat().st_size)


def author_column(columns):
    for name in ("author_id", "author"):
        if name in columns:
            return name
    sys.exit("ERROR: Could not find an author column. Columns: " + str(list(columns)))


def main():
    main_csv = find_main_csv()
    print("Using file:", main_csv)
    print("Size (MB):", round(main_csv.stat().st_size / 1e6, 1))

    peek = pd.read_csv(main_csv, nrows=5)
    print("\nColumns:", list(peek.columns))
    print("Using author column:", author_column(peek.columns))

    author_out = Counter()
    n_rows = 0
    n_in = 0

    print("\nScanning whole file in chunks (this can take 1-3 minutes)...")
    for chunk in pd.read_csv(main_csv, chunksize=200_000):
        n_rows += len(chunk)
        col = author_column(chunk.columns)
        if "inbound" in chunk.columns:
            inbound = chunk["inbound"].astype(bool)
            n_in += int(inbound.sum())
            out = chunk.loc[~inbound, col]
        else:
            out = chunk[col]
        author_out.update(out.value_counts().to_dict())

    print("\nTotal rows:", n_rows)
    print("Inbound (customer) rows:", n_in)
    print("\nTop 25 authors of outbound (company) tweets:")
    for author, cnt in author_out.most_common(25):
        print(f"{cnt:>8}  {author}")


if __name__ == "__main__":
    main()
