import json
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    df = pd.read_csv(ROOT / "eval" / "intent_predictions.csv")
    df = df.dropna(subset=["confidence"])
    df["correct"] = (df["true_intent"] == df["pred_intent"]).astype(int)
    bins = np.linspace(0, 1, 11)
    df["bin"] = pd.cut(df["confidence"], bins=bins, include_lowest=True)
    g = df.groupby("bin", observed=True).agg(n=("correct", "size"), mean_conf=("confidence", "mean"), mean_acc=("correct", "mean"))
    g.to_csv(ROOT / "eval" / "calibration_report.csv")
    print("| confidence bucket | n | mean confidence | mean accuracy |")
    print("|---|---|---|---|")
    for row in g.itertuples():
        print(f"| {row.Index} | {row.n} | {row.mean_conf:.2f} | {row.mean_acc:.2f} |")
    ece = float((g["n"] / len(df) * (g["mean_conf"] - g["mean_acc"]).abs()).sum())
    buckets = [{"bin": str(r.Index), "n": int(r.n), "mean_conf": round(float(r.mean_conf), 4), "mean_acc": round(float(r.mean_acc), 4)} for r in g.itertuples()]
    (ROOT / "eval" / "calibration_report.json").write_text(json.dumps({"ece": round(ece, 4), "buckets": buckets}))
    print(f"\nExpected Calibration Error (ECE, 10 bins): {ece:.3f}")
    print("Interpretation: |mean_conf - mean_acc| per bucket; ECE near 0 = calibrated.")

if __name__ == "__main__":
    main()

