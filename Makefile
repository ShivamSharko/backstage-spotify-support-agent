.PHONY: setup sample extract eval-intent eval-replies baselines quick

setup:
	python -m venv .venv
	pip install -r requirements.txt

sample:
	python scripts/sample_brand.py SpotifyCares

extract:
	python scripts/extract_replies.py

eval-intent:
	python scripts/evaluate.py

eval-replies:
	python scripts/evaluate_advanced.py

baselines:
	python scripts/run_baselines.py

quick:
	@echo "Running quick 2026-aligned evaluation (Dense RAG + PII Redaction)..."
	python scripts/evaluate_advanced.py
