import re
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
RISK_RE = re.compile(r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b')
PROFANITY_RE = re.compile(r'\b(?:fuck|shit|bitch|kill)\w*\b')

def keyword_flag(text):
    t = str(text).lower()
    if RISK_RE.search(t): return True
    if ('cancel' in t) and any(w in t for w in ["can't", "cannot", "unable", "won't"]): return True
    if PROFANITY_RE.search(t): return True
    return False

def evaluate(df, conf_t, ret_t):
    esc = (df['confidence'] < conf_t) | (df['retrieval_score'] < ret_t) | df['kw']
    auto = ~esc
    n_auto = int(auto.sum())
    misses = int((auto & df['true_escalate']).sum())
    true_risks = int(df['true_escalate'].sum())
    return n_auto / len(df), (misses / n_auto if n_auto else 0.0), (misses / true_risks if true_risks else 0.0)

def main():
    df = pd.read_csv(ROOT / "eval" / "risk_engine_results.csv")
    df['true_escalate'] = df['true_escalate'].astype(bool)
    df['kw'] = df['text'].apply(keyword_flag)

    rows = []
    for conf_t in np.arange(0.50, 0.96, 0.05):
        for ret_t in np.arange(0.20, 0.61, 0.05):
            a, v, r = evaluate(df, conf_t, ret_t)
            rows.append({"conf_thresh": round(conf_t, 2), "ret_thresh": round(ret_t, 2),
                         "auto_handle_rate": round(a, 4), "volume_false_auto": round(v, 4), "risk_miss_rate": round(r, 4)})
    grid = pd.DataFrame(rows)
    grid.to_csv(ROOT / "eval" / "calibration_grid.csv", index=False)

    X = df[['confidence', 'retrieval_score']].values
    y = df['true_escalate'].astype(int).values
    lr = LogisticRegression(class_weight='balanced', max_iter=1000).fit(X, y)
    prob = lr.predict_proba(X)[:, 1]

    best = None
    for t in np.arange(0.05, 0.96, 0.05):
        esc = (prob >= t) | df['kw']
        auto = ~esc
        misses = int((auto & df['true_escalate']).sum())
        true_risks = int(df['true_escalate'].sum())
        r = misses / true_risks if true_risks else 0
        a = auto.mean()
        if r <= 0.25 and (best is None or a > best['auto_handle_rate']):
            best = {"prob_thresh": round(float(t), 2), "auto_handle_rate": round(float(a), 4), "risk_miss_rate": round(float(r), 4)}

    out = {
        "mode": "calibrated_logistic",
        "coefficients": {"confidence": float(lr.coef_[0][0]), "retrieval_score": float(lr.coef_[0][1])},
        "intercept": float(lr.intercept_[0]),
        "prob_thresh": best["prob_thresh"] if best else 0.5,
        "expected_auto_handle_rate": best["auto_handle_rate"] if best else 0.0,
        "expected_risk_miss_rate": best["risk_miss_rate"] if best else 1.0,
        "note": "Fitted in-sample on the 200-row golden set; production would fit on a held-out split."
    }
    (ROOT / "configs").mkdir(exist_ok=True)
    (ROOT / "configs" / "thresholds.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print("\nBest grid operating points (risk_miss <= 0.25):")
    print(grid[grid['risk_miss_rate'] <= 0.25].sort_values('auto_handle_rate', ascending=False).head(8).to_string(index=False))

if __name__ == "__main__":
    main()

