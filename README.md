# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

An AI triage and drafting agent for Spotify customer support, built for the Hiver SDE take-home assignment. Features a 2026-aligned Dense Retrieval (RAG) pipeline, automated PII redaction, and a mathematical Risk & Confidence Engine for safe automation.

## 📊 Headline Results
- **Safe Auto-Handle Rate:** 76.50% of tickets can be automated, with a **4.58% False Auto-Handle Rate** (safely below the 5% production threshold).
- **Intent Classification:** 86% Accuracy / 0.84 Macro F1 (Heavily outperforms Simple Keyword Baseline at 60%).
- **Reply Safety:** 5.00 / 5 (Perfect score due to automated PII Redaction).
- **Retrieval:** Dense Vector Search using `all-MiniLM-L6-v2` over 43,000 historical replies.

*Note: See `REPORT.md` for a detailed breakdown of failure modes, Risk Engine math, and LLM Judge blindspots.*

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

### 3. Prepare Data & Run Evaluation
*Ensure the Kaggle dataset (`twcs.csv`) is placed inside `data/raw/twcs/`.*

To run the 2026-aligned pipeline (Dense RAG + PII Redaction):
```bash
make quick
```
*(Note: On Windows, if `make` is not installed, run `python scripts/evaluate_advanced.py` directly).*

To run the mathematical Risk & Confidence Engine to calculate the Safe Auto-Handle Rate:
```bash
python scripts/calculate_safe_autohandle.py
```

To compare against Trivial and Simple baselines:
```bash
make baselines
```

## 📁 Project Structure
- `scripts/`: Runnable pipeline scripts (sampling, baselines, advanced RAG, evaluation).
- `src/`: Modular components (PII redaction, Dense Retrieval engine).
- `prompts/`: Version-controlled LLM prompt templates.
- `data/`: Raw data, sampled brand data, and historical retrieval corpus.
- `eval/`: The 200-tweet Golden Set and evaluation results.
- `REPORT.md`: Detailed analysis, baselines, failure modes, and decision log.
