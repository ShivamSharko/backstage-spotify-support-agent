# REVIEW.md — Live-Round Cheat Sheet
How to probe and modify this system quickly during a live review.
Two implementation surfaces exist: the offline evaluation pipeline (Python; source of every headline number) and the live demo (web/ + Vercel serverless; simplified policy). Safety-rule changes must be synced across both — the duplication is listed explicitly so nobody drifts it silently.

## Offline pipeline (Python — all headline numbers)
- Change the escalation operating point: edit prob_thresh in configs/thresholds.json (or re-fit with python scripts/calibrate_gates.py), then re-run python scripts/calculate_safe_autohandle.py.
- Swap or add models: edit ModelRouter.models in src/router.py (order = priority). The router self-heals on 404/429 and logs per-model usage.
- Add an intent: extend the allowed list in prompts/intent.md (used by evaluate.py and evaluate_advanced.py), AND the inline sys_prompt in scripts/calculate_safe_autohandle.py, AND the JS list in web/api/pipeline.js; label rows in eval/golden_set.csv; re-run evaluate.py and run_baselines.py.
- Tighten PII rules: regexes in src/pii.py, pinned by tests/test_pii.py; mirror them in the RE map of web/api/pipeline.js for the demo.
- Grounding rules: trusted hosts + whitelist in src/verifier.py, pinned by tests/test_verifier.py. The demo does not run the verifier — disclosed in the demo footer.
- Escalation keywords: src/policy.py (RISK_RE now includes `sue\w*` to catch "sues"/"suing"), pinned by tests/test_policy.py (includes the sue-in-issue regression plus a plural test); mirror the exact regex (including profanity) in RE.risk of web/api/pipeline.js.
- Reproduce headline numbers: README quickstart sequence; artifacts in eval/*.csv.
- Judge rubric: prompts/judge.md; human agreement via human_* columns in eval/reply_eval_advanced.csv + scripts/calculate_agreement.py.
- Offline checks (no API key needed): pytest -q (14 tests).

## Live demo (web/ + Vercel serverless)
- Endpoint: web/api/pipeline.js — own MODELS fallback list, JS ports of the PII regexes, risk keywords and intent taxonomy; lexical evidence over web/evidence.json; policy = keyword backstop + LLM risk + confidence gate (no calibrated retrieval gate — disclosed in the UI).
- Key handling: GROQ_API_KEY lives only in Vercel environment variables; never in client code or in the repo.
- Redeploy: push to main; Vercel (root directory web) redeploys automatically.

## Rate limits (Groq free tier, March 2026, per organization)
- Binding caps here: openai/gpt-oss-120b 30 RPM / 1,000 RPD / 8,000 TPM / 200,000 TPD; qwen 27B-class ~1,000 RPD; Python router workhorse: allam-2-7b (30 RPM / 7,000 RPD / 500K TPD); the demo fallback chain ends at llama-3.1-8b-instant (14,400 RPD). You hit whichever axis arrives first.
- Router behaviour: on 429 the cooldown parses Groq's "try again in …" message; daily-budget (TPD/RPD) 429s get 6-hour cooldowns; 404 removes the model permanently.
- Headroom before 429: x-ratelimit-remaining-requests / -tokens and x-ratelimit-reset-tokens enable precise backoff (queued as REPORT §6 item 7). Cached tokens do not count toward limits, so stable system prompts stretch the budget. Extra keys under the same org share one bucket — they do not multiply limits.
