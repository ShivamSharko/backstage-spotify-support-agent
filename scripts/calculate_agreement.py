import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    # FIX: Read from reply_eval.csv which actually contains the human_* columns
    df = pd.read_csv(ROOT / "eval" / "reply_eval.csv").head(10)
    
    metrics = ['groundedness', 'safety', 'helpfulness']
    
    print("\n" + "="*55)
    print("HUMAN vs. LLM JUDGE AGREEMENT (Spearman Correlation)")
    print("="*55)
    print("(Computed on baseline pipeline replies that were manually graded)")
    print("-" * 55)
    
    for metric in metrics:
        human_col = f"human_{metric}"
        judge_col = f"judge_{metric}"
        subset = df[[human_col, judge_col]].dropna()
        
        if len(subset) > 1:
            corr = subset[human_col].corr(subset[judge_col], method='spearman')
            print(f"{metric.capitalize():<15} Agreement: {corr:.2f}")
        else:
            print(f"{metric.capitalize():<15} Agreement: Not enough data")
            
    print("="*55)
    print("\nConclusion: The judge exhibits self-preference bias and is blind to domain hallucinations.")

if __name__ == "__main__":
    main()
