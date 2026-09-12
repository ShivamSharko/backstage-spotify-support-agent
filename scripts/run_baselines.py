import pandas as pd
import re
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]

def trivial_intent(text): return "other"
def trivial_escalation(text): return True

def simple_intent(text):
    t = str(text).lower()
    if any(w in t for w in ['password', 'login', 'sign in', 'hacked', 'stolen', 'account']): return 'account_login'
    if any(w in t for w in ['charge', 'refund', 'premium', 'billing', 'invoice', 'cancel']): return 'billing_payment'
    if any(w in t for w in ['crash', 'bug', "won't play", 'freeze', 'error', "doesn't work"]): return 'app_bug'
    if any(w in t for w in ['add feature', 'lyrics', 'wish', 'suggest', 'how do i']): return 'feature_request'
    return 'other'

def simple_escalation(text):
    t = str(text).lower()
    risk_pattern = r'\b(?:hack\w*|stol\w*|steal\w*|fraud\w*|lawyer\w*|legal\w*|sue|sued|suing|unauthoriz\w*|compromis\w*|phish\w*|scam\w*|threat\w*)\b'
    has_risk = bool(re.search(risk_pattern, t))
    has_dead_end = ('cancel' in t) and any(w in t for w in ["can't", "cannot", "unable", "won't"])
    return has_risk or has_dead_end

def main():
    df = pd.read_csv(ROOT / "eval" / "golden_set.csv").dropna(subset=['true_intent', 'should_escalate'])
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'
    true_intents = df['true_intent'].tolist()
    true_esc = df['should_escalate'].tolist()

    t_ints = [trivial_intent(t) for t in df['text']]
    t_esc = [trivial_escalation(t) for t in df['text']]
    s_ints = [simple_intent(t) for t in df['text']]
    s_esc = [simple_escalation(t) for t in df['text']]

    preds_path = ROOT / "eval" / "intent_predictions.csv"
    if not preds_path.exists():
        print("ERROR: Run 'python scripts/evaluate.py' first.")
        return

    preds_df = pd.read_csv(preds_path)
    assert len(df) == len(preds_df), "Mismatch in row count. Re-run evaluate.py."
    
    m_ints = preds_df['pred_intent'].tolist()
    m_esc = preds_df['pred_escalate'].tolist()

    print("\n" + "="*75)
    print("SYSTEM COMPARISON TABLE")
    print("="*75)
    print(f"{'Metric':<25} | {'Trivial':<15} | {'Simple (Keywords)':<15} | {'Main System (LLM)':<15}")
    print("-" * 75)
    print(f"{'Intent Accuracy':<25} | {accuracy_score(true_intents, t_ints):>13.2%} | {accuracy_score(true_intents, s_ints):>13.2%} | {accuracy_score(true_intents, m_ints):>13.2%}")
    print(f"{'Intent Macro F1':<25} | {f1_score(true_intents, t_ints, average='macro', zero_division=0):>15.2f} | {f1_score(true_intents, s_ints, average='macro', zero_division=0):>15.2f} | {f1_score(true_intents, m_ints, average='macro', zero_division=0):>15.2f}")
    print("-" * 75)
    print(f"{'Escalation Precision':<25} | {precision_score(true_esc, t_esc, zero_division=0):>15.2f} | {precision_score(true_esc, s_esc, zero_division=0):>15.2f} | {precision_score(true_esc, m_esc, zero_division=0):>15.2f}")
    print(f"{'Escalation Recall':<25} | {recall_score(true_esc, t_esc, zero_division=0):>15.2f} | {recall_score(true_esc, s_esc, zero_division=0):>15.2f} | {recall_score(true_esc, m_esc, zero_division=0):>15.2f}")
    print("="*75)

if __name__ == "__main__":
    main()
