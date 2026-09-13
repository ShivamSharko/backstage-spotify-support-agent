# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

AI triage, grounded reply drafting, and escalation for Spotify customer support. Dense RAG over 43k historical replies, pre-LLM PII redaction, a symbolic grounding verifier, a calibrated risk engine, and a self-healing multi-model fallback router.

## Headline results (verbatim harness output, single run)
- Intent: **87.50% accuracy / 0.89 macro F1** (trivial 49.00% / 0.13; simple keywords 60.00% / 0.46).
- Risk Engine v3: **auto-handle 61.00%**, **volume false auto-handle 2.46%** (≤5% bar met), **risk miss 18.75%** (3/16), recall 0.81.
- Grounding verifier: 0 hallucinated URLs survived in the 20-reply test.
- Judge (20 replies): groundedness 4.75/5, safety 3.85/5, helpfulness 3.85/5.
- Human–judge agreement: see [REPORT.md](REPORT.md) (reproduce via scripts/calculate_agreement.py).
- Router disclosure: most requests served by qwen/qwen3.8-27b after gpt-oss-120b's daily token budget exhausted; metrics characterize the router-backed system.

## Quickstart (under 15 minutes)
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add your Groq API key
python scripts/sample_brand.py SpotifyCares
python scripts/extract_replies.py
python scripts/evaluate.py
python scripts/run_baselines.py
python scripts/calculate_safe_autohandle.py
python scripts/calibrate_gates.py
python scripts/calculate_safe_autohandle.py
python scripts/evaluate_advanced.py
python scripts/calculate_agreement.py
```

## Project structure
- `scripts/`: runnable pipeline (sampling, baselines, calibration, risk engine, RAG eval, agreement).
- `src/`: modular components (PII redaction, dense retrieval, verifier, model router).
- `prompts/`: version-controlled LLM prompt templates loaded at runtime.
- `configs/`: fitted calibration thresholds.
- `data/`: sampled brand data and retrieval corpus.
- `eval/`: golden set, predictions, risk-engine breakdowns, reply evaluations.
- [REPORT.md](REPORT.md): full analysis, failure modes, misleading-number disclosures, decision log.
- [CITATION.md](CITATION.md): borrowed ideas and papers.

## Known limitations
- Mixed-model evaluation (router fallback) introduces model-mix variance; single-model re-run pending the daily reset.
- Calibration fitted in-sample on 200 rows.
- The judge shares the generator model family and is lenient on URLs; the symbolic verifier is the real guard.
- Retrieval popularity bias on context-free fragments.
