import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    path = ROOT / "eval" / "reply_eval_advanced.csv"
    df = pd.read_csv(path).head(10)
    metrics = ['groundedness', 'safety', 'helpfulness']
    missing = [m for m in metrics if f"human_{m}" not in df.columns]
    if missing:
        print(f"ERROR: columns {['human_' + m for m in missing]} missing in reply_eval_advanced.csv.")
        print("Open the CSV, grade the first 10 rows in those columns, save, then re-run.")
        return

    print("\n" + "="*55)
    print("HUMAN vs. LLM JUDGE AGREEMENT (Spearman, advanced pipeline)")
    print("="*55)
    for metric in metrics:
        subset = df[[f"human_{metric}", f"judge_{metric}"]].dropna()
        if len(subset) > 1:
            corr = subset[f"human_{metric}"].corr(subset[f"judge_{metric}"], method='spearman')
            print(f"{metric.capitalize():<15} Agreement: {corr:.2f}")
        else:
            print(f"{metric.capitalize():<15} Agreement: Not enough data")
    print("="*55)

if __name__ == "__main__":
    main()
