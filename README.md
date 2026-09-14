# Backstage — AI Support Agent for SpotifyCares
*Named after Spotify support's own words in our training data: "We'll take a look backstage."*

AI triage, grounded reply drafting, and escalation for Spotify customer support. Dense RAG over 43k historical replies, pre-LLM PII redaction, a symbolic grounding verifier, a calibrated risk engine, and a self-healing multi-model fallback router.

## Headline results (verbatim harness output, single run)
**Live demo:** https://backstage-spotify-support-agent.vercel.app/ — serverless proxy runs the intent/risk/draft prompts with lexical evidence and a simplified policy; headline numbers come from the offline dense-retrieval pipeline.
- **Intent classification:** 83.00% accuracy / 0.81 Macro F1 (Trivial: 49.00% / 0.13; Simple: 60.00% / 0.46). Intent accuracy is within ±2% of prior runs due to model-mix variance across the router-backed pipeline.
- **Risk Engine v3:** Auto-Handle 59.00%, Volume False Auto-Handle 1.69%, Risk Miss 12.50%, Recall 88%.
- **Calibration ECE:** 0.073 (10-bin Expected Calibration Error on verbalized confidence).
- **Judge scores:** Groundedness 4.85/5, Safety 4.20/5, Helpfulness 4.20/5.
- **Human-Judge Agreement (20 graded rows):** Groundedness -0.15 (judge is anti-correlated with humans, proving the symbolic verifier is necessary), Safety 0.84, Helpfulness -0.03.
- **Grounding Verifier:** 0 hallucinated URLs in 20-test set.

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
python scripts/calibration_report.py
python scripts/operating_curve.py
python scripts/export_demo_bundle.py
```

**Live demo deployment:** The frontend and serverless API live in `web/`. When deploying to Vercel, set **Root Directory = `web`** in the project settings (under Settings → General) so Vercel recognizes `api/pipeline.js` as a serverless function. Add your `GROQ_API_KEY` as an environment variable in Vercel (never commit it to the repo). The demo is already live at the URL listed in the headline results section above.

## Project structure
- `scripts/`: runnable pipeline (sampling, baselines, calibration, risk engine, RAG eval, agreement).
- `src/`: modular components (PII redaction, dense retrieval, verifier, model router).
- `prompts/`: version-controlled LLM prompt templates loaded at runtime.
- `configs/`: fitted calibration thresholds.
- `data/`: sampled brand data and retrieval corpus.
- `eval/`: golden set, predictions, risk-engine breakdowns, reply evaluations.
- [REPORT.md](REPORT.md): full analysis, failure modes, misleading-number disclosures, decision log.
- [CITATION.md](CITATION.md): borrowed ideas and papers.
- `tests/` + `.github/workflows/offline-tests.yml`: offline regression suite (no API key) pinning every bug the audits found.
- `REVIEW.md`: live-round modification cheat sheet.

## Known limitations
- Mixed-model evaluation (router fallback) introduces model-mix variance; single-model re-run pending the daily reset.
- Calibration fitted in-sample on 200 rows.
- The judge shares the generator model family and is lenient on URLs; the symbolic verifier is the real guard.
- Retrieval popularity bias on context-free fragments.
