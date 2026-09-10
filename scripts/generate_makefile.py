from pathlib import Path

# We use \t to guarantee actual TAB characters, which Makefiles strictly require.
makefile_content = """.PHONY: setup sample extract eval-intent eval-replies baselines quick

setup:
\tpython -m venv .venv
\tpip install -r requirements.txt

sample:
\tpython scripts/sample_brand.py SpotifyCares

extract:
\tpython scripts/extract_replies.py

eval-intent:
\tpython scripts/evaluate.py

eval-replies:
\tpython scripts/evaluate_advanced.py

baselines:
\tpython scripts/run_baselines.py

quick:
\t@echo "Running quick 2026-aligned evaluation (Dense RAG + PII Redaction)..."
\tpython scripts/evaluate_advanced.py
"""

with open("Makefile", "w", encoding="utf-8") as f:
    f.write(makefile_content)
print("SUCCESS: Makefile created with proper TAB indentation.")

