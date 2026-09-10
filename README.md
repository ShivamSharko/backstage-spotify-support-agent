# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

An AI triage and drafting agent for Spotify customer support, built for the Hiver SDE take-home assignment. Features a 2026-aligned Dense Retrieval (RAG) pipeline and automated PII redaction.

## 📊 Headline Results
- **Intent Classification:** 86% Accuracy / 0.84 Macro F1 (Heavily outperforms Simple Keyword Baseline at 60%).
- **Reply Safety:** 5.00 / 5 (Perfect score due to automated PII Redaction).
- **Retrieval:** Dense Vector Search using `all-MiniLM-L6-v2` over 43,000 historical replies.

*Note: See `REPORT.md` for a detailed breakdown of failure modes and LLM Judge blindspots.*

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
To evaluate intent classification against the 200-tweet Golden Set:
```bash
python scripts/evaluate.py
```

To run the 2026-aligned pipeline (Dense Retrieval + PII Redaction + Generation):
```bash
python scripts/evaluate_advanced.py
```

To compare against Trivial and Simple baselines:
```bash
python scripts/run_baselines.py
```

## 📁 Project Structure
- `scripts/`: Runnable pipeline scripts (sampling, baselines, advanced RAG, evaluation).
- `src/`: Modular components (PII redaction, Dense Retrieval engine).
- `data/`: Raw data, sampled brand data, and historical retrieval corpus.
- `eval/`: The 200-tweet Golden Set and evaluation results.
- `REPORT.md`: Detailed analysis, baselines, failure modes, and decision log.
