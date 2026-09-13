import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.policy import keyword_flag

def main():
    preds = pd.read_csv(ROOT / "eval" / "intent_predictions.csv")
    risk = pd.read_csv(ROOT / "eval" / "risk_engine_results.csv")
    replies = pd.read_csv(ROOT / "eval" / "reply_eval_advanced.csv")
    curve = pd.read_csv(ROOT / "eval" / "operating_curve.csv")
    cfg = json.loads((ROOT / "configs" / "thresholds.json").read_text())
    corpus = pd.read_csv(ROOT / "data" / "retrieval" / "spotify_replies.csv")

    c = cfg["coefficients"]
    df = risk.copy()
    z = c["confidence"] * df["confidence"] + c["retrieval_score"] * df["retrieval_score"] + cfg["intercept"]
    z = np.clip(z, -700, 700)
    df["risk_score"] = 1 / (1 + np.exp(-z))
    df["kw"] = df["text"].apply(keyword_flag)
    df["true_escalate"] = df["true_escalate"].astype(bool)

    auto = ~df["pred_escalate"]
    misses = int((auto & df["true_escalate"]).sum())
    tr = int(df["true_escalate"].sum())
    agree = {}
    for m in ["groundedness", "safety", "helpfulness"]:
        hc = f"human_{m}"
        if hc in replies.columns:
            sub = replies[[hc, f"judge_{m}"]].dropna()
            if len(sub) < 3:
                agree[m] = None
            else:
                c = sub[hc].corr(sub[f"judge_{m}"], method="spearman")
                agree[m] = None if pd.isna(c) else round(float(c), 2)

    demo = {
        "headline": {
            "auto_handle": round(float(auto.mean()) * 100, 2),
            "volume_false_auto": round(misses / int(auto.sum()) * 100, 2),
            "risk_miss": round(misses / tr * 100, 2),
            "macro_f1": round(f1_score(preds["true_intent"], preds["pred_intent"], average="macro", zero_division=0), 2),
            "accuracy": round(accuracy_score(preds["true_intent"], preds["pred_intent"]) * 100, 2),
            "prob_thresh": cfg["prob_thresh"],
        },
        "agreement": agree,
        "curve": curve.to_dict(orient="records"),
        "tickets": [{"risk_score": round(float(r.risk_score), 4), "kw": bool(r.kw), "true_escalate": bool(r.true_escalate)} for r in df.itertuples()],
    }
    web = ROOT / "web"
    (web / "data").mkdir(parents=True, exist_ok=True)
    (web / "data" / "demo.json").write_text(json.dumps(demo))

    ev = corpus["text"].dropna().astype(str)
    ev = ev[ev.str.len() > 40]
    sample = ev.sample(n=1500, random_state=42).tolist()
    (web / "evidence.json").write_text(json.dumps(sample))
    print(f"wrote web/data/demo.json ({len(demo['tickets'])} tickets) and web/evidence.json ({len(sample)} replies)")

if __name__ == "__main__":
    main()

