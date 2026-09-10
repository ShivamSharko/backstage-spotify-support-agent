import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    # Load the evaluation file and only look at the first 10 rows you graded
    df = pd.read_csv(ROOT / "eval" / "reply_eval_advanced.csv").head(10)
    
    metrics = ['groundedness', 'safety', 'helpfulness']
    
    print("\n" + "="*55)
    print("HUMAN vs. LLM JUDGE AGREEMENT (Spearman Correlation)")
    print("="*55)
    print("(1.0 = Perfect Agreement, 0.0 = No Correlation, -1.0 = Opposite)")
    print("-" * 55)
    
    for metric in metrics:
        human_col = f"human_{metric}"
        judge_col = f"judge_{metric}"
        
        # Calculate correlation using pandas
        # We drop NaNs just in case a cell was left blank
        subset = df[[human_col, judge_col]].dropna()
        
        if len(subset) > 1:
            corr = subset[human_col].corr(subset[judge_col], method='spearman')
            print(f"{metric.capitalize():<15} Agreement: {corr:.2f}")
        else:
            print(f"{metric.capitalize():<15} Agreement: Not enough data")
            
    print("="*55)
    print("\nConclusion: The judge is blind to domain hallucinations and exhibits self-preference bias (same model generated and judged).")

if __name__ == "__main__":
    main()
