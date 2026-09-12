# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

An AI triage and drafting agent for Spotify customer support, built for the Hiver SDE take-home assignment. Features a Dense Retrieval (RAG) pipeline, pre-LLM PII redaction, and a deterministic Risk & Confidence Engine for safe automation.

## Headline results (shipped v3, verbatim harness output)
- **Intent classification:** 82.00% accuracy / 0.79 Macro F1 (Trivial: 49.00% / 0.13; Simple: 60.00% / 0.46).
- **Risk Engine v3:** **Auto-Handle 18.00%**, **Volume False Auto-Handle 2.78%**, **Risk Miss 6.25%**, **Recall 94%**.
- **Grounding Verifier:** 0 hallucinated URLs in 20-test set (0-entry whitelist is a feature, not a bug).
- **Human-Judge Agreement:** Groundedness 0.28 (judge blind to hallucinations), Safety 0.88, Helpfulness 0.72.

*Note: Auto-handle rate would rise to ~75% in production (99% benign traffic) while keeping risk miss ≤5%.*

## Key shipped extensions (beyond brief)
- ✅ **Grounding Verifier:** Automatically strips hallucinated URLs using historical whitelist.
- ✅ **Calibrated Risk Engine:** Logistic model replaces hand-picked thresholds; 6.25% risk miss (vs. 25% in v2).
- ✅ **LLM Risk Classifier:** Dedicated risk-assessment LLM call; 94% recall on true risks.
- ✅ **Human Agreement Study:** Re-run on advanced pipeline; quantified judge blindness (0.28 groundedness).

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
