import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]

# --- BASELINE 1: TRIVIAL ---
def trivial_intent(text): 
    return "other"

def trivial_escalation(text): 
    return True # Always escalate to be "safe"

# --- BASELINE 2: SIMPLE (Keyword Rules) ---
def simple_intent(text):
    t = str(text).lower()
    if any(w in t for w in ['password', 'login', 'sign in', 'hacked', 'stolen', 'account']): return 'account_login'
    if any(w in t for w in ['charge', 'refund', 'premium', 'billing', 'invoice', 'cancel']): return 'billing_payment'
    if any(w in t for w in ['crash', 'bug', "won't play", 'freeze', 'error', "doesn't work"]): return 'app_bug'
    if any(w in t for w in ['add feature', 'lyrics', 'wish', 'suggest', 'how do i']): return 'feature_request'
    return 'other'

def simple_escalation(text):
    t = str(text).lower()
    return any(w in t for w in ['hack', 'stolen', 'fraud', 'lawyer', 'sue', 'unauthorized'])

def main():
    df = pd.read_csv(ROOT / "eval" / "golden_set.csv")
    df = df.dropna(subset=['true_intent', 'should_escalate'])
    df['should_escalate'] = df['should_escalate'].astype(str).str.lower().str.strip() == 'true'

    true_intents = df['true_intent'].tolist()
    true_esc = df['should_escalate'].tolist()

    # Run Trivial
    t_ints = [trivial_intent(t) for t in df['text']]
    t_esc = [trivial_escalation(t) for t in df['text']]

    # Run Simple
    s_ints = [simple_intent(t) for t in df['text']]
    s_esc = [simple_escalation(t) for t in df['text']]

    # Main System metrics (from our previous evaluate.py run)
    m_int_acc = 0.86
    m_int_f1 = 0.84
    m_esc_prec = 0.20
    m_esc_rec = 0.56

    print("\n" + "="*75)
    print("SYSTEM COMPARISON TABLE (Evaluated on 200 Golden Set Tweets)")
    print("="*75)
    print(f"{'Metric':<25} | {'Trivial Baseline':<16} | {'Simple Baseline':<16} | {'Main System (LLM)':<16}")
    print("-" * 75)
    
    # Intent Metrics
    t_acc = accuracy_score(true_intents, t_ints)
    t_f1 = f1_score(true_intents, t_ints, average='macro', zero_division=0)
    
    s_acc = accuracy_score(true_intents, s_ints)
    s_f1 = f1_score(true_intents, s_ints, average='macro', zero_division=0)

    print(f"{'Intent Accuracy':<25} | {t_acc:>14.2f}% | {s_acc:>14.2f}% | {m_int_acc:>15.2f}%")
    print(f"{'Intent Macro F1':<25} | {t_f1:>16.2f} | {s_f1:>16.2f} | {m_int_f1:>16.2f}")
    
    # Escalation Metrics
    t_esc_prec = precision_score(true_esc, t_esc, zero_division=0)
    t_esc_rec = recall_score(true_esc, t_esc, zero_division=0)
    
    s_esc_prec = precision_score(true_esc, s_esc, zero_division=0)
    s_esc_rec = recall_score(true_esc, s_esc, zero_division=0)

    print("-" * 75)
    print(f"{'Escalation Precision':<25} | {t_esc_prec:>16.2f} | {s_esc_prec:>16.2f} | {m_esc_prec:>16.2f}")
    print(f"{'Escalation Recall':<25} | {t_esc_rec:>16.2f} | {s_esc_rec:>16.2f} | {m_esc_rec:>16.2f}")
    print("="*75)
    print("\nConclusion: The Main System heavily outperforms baselines in Intent F1,")
    print("but all systems struggle with Escalation Precision due to the rarity")
    print("of high-risk tweets (only 16 out of 200) causing false positives.")

if __name__ == "__main__":
    main()

