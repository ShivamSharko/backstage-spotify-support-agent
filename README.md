# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

An AI triage and drafting agent for Spotify customer support, built for the Hiver SDE take-home assignment. Features a Dense Retrieval (RAG) pipeline, pre-LLM PII redaction, and a deterministic Risk & Confidence Engine for safe automation.

## Headline results (verbatim harness output, single run)
- Intent classification: **82.00% accuracy / 0.79 Macro F1** (Trivial baseline 49.00% / 0.13; Simple keyword baseline 60.00% / 0.46).
- Escalation rule layer: **Precision 0.79 / Recall 0.69**.
- Risk & Confidence Engine: **Auto-Handle 52.00%**, **Volume False Auto-Handle 3.85%**, **Risk Miss 25.00%** (4 of 16 true risks).
- Reply quality (LLM judge, 20 replies): Groundedness 4.70/5, Safety 5.00/5, Helpfulness 4.70/5. *The Safety score reflects a lenient same-model judge; a human pass graded DM-based PII asks 4/5. See REPORT.md.*

Reproduce with: `python scripts/evaluate.py`, `python scripts/run_baselines.py`, `python scripts/calculate_safe_autohandle.py`. Intent metrics may shift ~1-2% between runs (LLM variance); per-tweet escalation reasons are logged in `eval/risk_engine_results.csv`.

## Quickstart (Under 15 Minutes)

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
```bash
python scripts/sample_brand.py SpotifyCares
python scripts/extract_replies.py
```

Run the Dense RAG pipeline (PII redaction + retrieval + judge):
```bash
make quick
```
*(On Windows without make: `python scripts/evaluate_advanced.py`)*

Reproduce the headline table:
```bash
python scripts/evaluate.py
python scripts/run_baselines.py
python scripts/calculate_safe_autohandle.py
```

Human vs Judge agreement (8 manually graded rows):
```bash
python scripts/calculate_agreement.py
```

## Project Structure
- `scripts/`: Runnable pipeline (sampling, baselines, advanced RAG, risk engine, evaluation).
- `src/`: Modular components (PII redaction, Dense Retrieval engine).
- `prompts/`: Version-controlled LLM prompt templates, loaded at runtime.
- `data/`: Raw data, sampled brand data, and historical retrieval corpus.
- `eval/`: 200-tweet Golden Set, saved predictions, risk-engine breakdowns, reply evaluations.
- `REPORT.md`: Full analysis, failure modes, misleading-number disclosures, decision log.
- `CITATION.md`: Borrowed ideas and papers.

## Known Limitations
- Dense retrieval can still surface popular generic replies over rare specific resolutions.
- The LLM judge shares the generator model and is lenient toward hallucinated URLs; human agreement is modest (Safety 0.61, Helpfulness 0.35, Groundedness NaN).
- Escalation gates (confidence 0.7, retrieval 0.4) are chosen operating points, not calibrated thresholds.
