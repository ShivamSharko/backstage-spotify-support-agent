import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pii import redact_pii
from src.policy import keyword_flag
from src.retrieval import DenseRetriever

def main():
    preds = pd.read_csv(ROOT / "eval" / "intent_predictions.csv")
    risk = pd.read_csv(ROOT / "eval" / "risk_engine_results.csv")
    replies = pd.read_csv(ROOT / "eval" / "reply_eval_advanced.csv")
    curve = pd.read_csv(ROOT / "eval" / "operating_curve.csv")
    calib = pd.read_csv(ROOT / "eval" / "calibration_report.csv")
    cfg = json.loads((ROOT / "configs" / "thresholds.json").read_text())

    human_cols = [c for c in replies.columns if c.startswith("human_")]
    judge_cols = ["generated_reply", "verifier_violations", "judge_groundedness", "judge_safety", "judge_helpfulness"] + human_cols
    df = risk.merge(preds[["text", "pred_intent", "true_intent"]], on="text", how="left")
    df = df.merge(replies.rename(columns={"tweet": "text"})[["text"] + judge_cols], on="text", how="left")

    c = cfg["coefficients"]
    z = c["confidence"] * df["confidence"] + c["retrieval_score"] * df["retrieval_score"] + cfg["intercept"]
    df["risk_score"] = 1 / (1 + np.exp(-z))
    df["safe_text"] = df["text"].apply(redact_pii)
    df["kw"] = df["text"].apply(keyword_flag)
    df["true_escalate"] = df["true_escalate"].astype(bool)
    df["pred_escalate"] = df["pred_escalate"].astype(bool)

    print("Building evidence index (local embeddings, no API calls)...")
    retriever = DenseRetriever(str(ROOT / "data" / "retrieval" / "spotify_replies.csv"))
    want_evidence = df["generated_reply"].notna() | (~df["pred_escalate"] & df["true_escalate"]) | df["llm_risk"].astype(bool)
    evidence = {}
    for i, row in df[want_evidence].head(40).iterrows():
        evidence[row["text"]] = [e["text"] for e in retriever.search(row["safe_text"], top_k=3)]

    auto = ~df["pred_escalate"]
    misses = int((auto & df["true_escalate"]).sum())
    tr = int(df["true_escalate"].sum())
    g = calib.copy()
    ece = float((g["n"] / g["n"].sum() * (g["mean_conf"] - g["mean_acc"]).abs()).sum())
    agree = {}
    for m in ["groundedness", "safety", "helpfulness"]:
        hc, jc = f"human_{m}", f"judge_{m}"
        if hc in replies.columns:
            sub = replies[[hc, jc]].dropna()
            agree[m] = None if len(sub) < 3 else round(float(sub[hc].corr(sub[jc], method="spearman")), 2)

    def clean(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        if isinstance(v, (np.bool_, bool)):
            return bool(v)
        if isinstance(v, (np.floating, float)):
            return round(float(v), 4)
        if isinstance(v, (np.integer, int)):
            return int(v)
        return v

    tickets = []
    for _, r in df.iterrows():
        t = {k: clean(r[k]) for k in ["text", "safe_text", "true_intent", "pred_intent", "confidence",
                                      "retrieval_score", "risk_score", "kw", "llm_risk",
                                      "pred_escalate", "true_escalate", "reason"]}
        t["evidence"] = evidence.get(r["text"])
        if isinstance(r.get("generated_reply"), str):
            t["reply"] = r["generated_reply"]
            t["verifier_violations"] = clean(r["verifier_violations"])
            t["judge"] = {m: clean(r[f"judge_{m}"]) for m in ["groundedness", "safety", "helpfulness"]}
            t["human"] = {m: clean(r[f"human_{m}"]) for m in ["groundedness", "safety", "helpfulness"] if f"human_{m}" in r and pd.notna(r[f"human_{m}"])} or None
        tickets.append(t)

    demo = {
        "meta": {
            "headline": {
                "accuracy": round(accuracy_score(preds["true_intent"], preds["pred_intent"]) * 100, 2),
                "macro_f1": round(f1_score(preds["true_intent"], preds["pred_intent"], average="macro", zero_division=0), 2),
                "auto_handle": round(float(auto.mean()) * 100, 2),
                "volume_false_auto": round(misses / int(auto.sum()) * 100, 2),
                "risk_miss": round(misses / tr * 100, 2),
                "recall": round(float((df["pred_escalate"] & df["true_escalate"]).sum()) / tr, 2),
                "ece": round(ece, 3),
            },
            "agreement": agree,
            "judge_means": {m: round(float(replies[f"judge_{m}"].mean()), 2) for m in ["groundedness", "safety", "helpfulness"]},
            "coeffs": {"confidence": c["confidence"], "retrieval_score": c["retrieval_score"],
                       "intercept": cfg["intercept"], "prob_thresh": cfg["prob_thresh"]},
            "disclosure": "Most evaluation requests were served by qwen/qwen3.8-27b via the fallback router after gpt-oss-120b's daily token budget was exhausted. Metrics characterize the router-backed system.",
        },
        "curve": curve.to_dict(orient="records"),
        "calibration": calib.to_dict(orient="records"),
        "tickets": tickets,
    }
    out = ROOT / "docs" / "data"
    out.mkdir(parents=True, exist_ok=True)
    (out / "demo.json").write_text(json.dumps(demo))
    print(f"Wrote {out / 'demo.json'} with {len(tickets)} tickets.")

if __name__ == "__main__":
    main()

