# Backstage — AI Support Agent for SpotifyCares

*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

An AI triage and drafting agent for Spotify customer support, built for the Hiver SDE take-home assignment.

## 📊 Headline Results
- **Intent Classification:** 86% Accuracy / 0.84 Macro F1 on a 200-tweet hand-labelled Golden Set.
- **Reply Groundedness:** 4.95 / 5 (as scored by LLM-as-a-Judge).
- **Safe Auto-Handle Rate:** System correctly identifies high-risk escalation triggers (hacks, fraud) with 56% recall.

*Note: See `REPORT.md` for a detailed breakdown of why the headline numbers are misleading, including the LLM Judge's failure to catch domain hallucinations.*

## 🚀 Quickstart (Under 15 Minutes)

### 1. Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key
Copy `.env.example` to `.env` and add your Groq API key:
```bash
GROQ_API_KEY=your_key_here
MODEL_NAME=openai/gpt-oss-120b
```

### 3. Prepare Data
*Ensure the Kaggle dataset (`twcs.csv`) is placed inside `data/raw/twcs/`.*
```bash
python scripts/sample_brand.py SpotifyCares
python scripts/extract_replies.py
```

### 4. Run Evaluation
To evaluate intent classification and escalation against the Golden Set:
```bash
python scripts/evaluate.py
```

To generate replies and run the LLM-as-a-Judge:
```bash
python scripts/evaluate_replies.py
```

To check Human vs. Judge agreement (requires `eval/reply_eval.csv` to have human scores in first 10 rows):
```bash
python scripts/calculate_agreement.py
```

## 📁 Project Structure
- `scripts/`: Runnable pipeline scripts (sampling, retrieval, generation, evaluation).
- `data/`: Raw data, sampled brand data, and historical retrieval corpus.
- `eval/`: The 200-tweet Golden Set and evaluation results.
- `REPORT.md`: Detailed analysis, baselines, failure modes, and decision log.

## ⚠️ Known Limitations
- TF-IDF retrieval misses semantic similarities (e.g., "charged twice" -> "refund").
- LLM Judge is overly optimistic and misses specific UI/URL hallucinations.
- Escalation relies on brittle keyword matching, resulting in low precision.

