# REVIEW.md — Live-Round Cheat Sheet
How to probe and modify this system quickly during a live review.
- Change the escalation operating point: edit prob_thresh in configs/thresholds.json (or re-fit with python scripts/calibrate_gates.py), then re-run python scripts/calculate_safe_autohandle.py.
- Swap or add models: edit ModelRouter.models in src/router.py (order = priority). The router self-heals on 404/429 and logs per-model usage.
- Add an intent: extend the allowed list in prompts/intent.md, label rows in eval/golden_set.csv, re-run evaluate.py and run_baselines.py.
- Tighten PII rules: regexes in src/pii.py; pinned by tests/test_pii.py.
- Grounding rules: trusted hosts + whitelist in src/verifier.py; pinned by tests/test_verifier.py.
- Escalation keywords: src/policy.py; pinned by tests/test_policy.py (includes the sue-in-issue regression).
- Reproduce headline numbers: README quickstart sequence; artifacts in eval/*.csv.
- Judge rubric: prompts/judge.md; human agreement via human_* columns in eval/reply_eval_advanced.csv + scripts/calculate_agreement.py.
- Offline checks (no API key needed): pytest -q

