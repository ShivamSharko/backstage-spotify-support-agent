import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.policy import keyword_flag

def main():
    df = pd.read_csv(ROOT / "eval" / "risk_engine_results.csv")
    df["true_escalate"] = df["true_escalate"].astype(bool)
    df["kw"] = df["text"].apply(keyword_flag)
    cfg = json.loads((ROOT / "configs" / "thresholds.json").read_text())
    z = (cfg["coefficients"]["confidence"] * df["confidence"]
         + cfg["coefficients"]["retrieval_score"] * df["retrieval_score"]
         + cfg["intercept"])
    df["risk_score"] = 1 / (1 + np.exp(-z))
    tr = df["true_escalate"].sum()
    rows = []
    for t in np.arange(0.05, 0.96, 0.05):
        esc = (df["risk_score"] >= t) | df["kw"]
        auto = ~esc
        misses = int((auto & df["true_escalate"]).sum())
        rows.append({
            "threshold": round(float(t), 2),
            "auto_handle_rate": round(float(auto.mean()), 4),
            "volume_false_auto": round(misses / int(auto.sum()), 4) if auto.sum() else 0.0,
            "risk_miss_rate": round(misses / tr, 4) if tr else 0.0,
        })
    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "eval" / "operating_curve.csv", index=False)
    print(out.to_string(index=False))
    print(f"\nChosen operating point (configs/thresholds.json): prob_thresh = {cfg['prob_thresh']}")

if __name__ == "__main__":
    main()
