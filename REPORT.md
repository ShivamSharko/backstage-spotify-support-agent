# Backstage: Customer Support Agent — Hiver Take-Home Assignment

## 1. Problem Framing
**Brand chosen:** Spotify (SpotifyCares).
**Why:** Spotify has high volume (~43k support replies), clear digital intents, and historically provides actionable troubleshooting steps in public tweets.

**What "good" means:**
A "good" agent is safe, grounded, and operationally useful. It must correctly triage intents, retrieve semantically similar historical evidence, and draft replies that do not hallucinate. Most importantly, it must escalate high-risk issues without overwhelming human agents with false alarms.

**What I chose not to build:**
No live Twitter integration, no multi-turn conversation state manager, and no account-action execution (e.g., actually processing refunds). The scope is strictly classification, grounded drafting, and escalation decisions from historical public data.

## 2. System Design (2026-Aligned Architecture)
1. **PII Redaction:** Regex-based stripping of emails, phone numbers, and URLs before text reaches the LLM (`src/pii.py`).
2. **Intent Classifier:** Groq LLM with JSON structured output and verbalized confidence.
3. **Dense Retrieval (RAG):** `all-MiniLM-L6-v2` Sentence-Transformers over 43,265 historical Spotify replies; cosine similarity for semantic resolutions.
4. **Drafting:** LLM prompted with classified intent + top-3 retrieved matches; prompts version-controlled in `prompts/` and loaded at runtime.
5. **Two escalation layers:** a deterministic rule layer (word-boundary risk regex + intent gate), evaluated in the baseline table; and the Risk & Confidence Engine (rule layer + confidence < 0.7 gate + retrieval score < 0.4 gate), which produces the operational metrics.

## 3. Results on Golden Set (200 Hand-Labelled Examples)
All numbers below are exactly what the harness prints on a single run. Intent metrics may shift ~1-2% across runs due to LLM variance; per-tweet escalation reasons are logged in `eval/risk_engine_results.csv`.

### Baseline Comparison
| Metric | Trivial Baseline | Simple Baseline (Keywords) | Main System (LLM + Dense RAG) |
| :--- | :--- | :--- | :--- |
| **Intent Accuracy** | 49.00% | 60.00% | **82.00%** |
| **Intent Macro F1** | 0.13 | 0.46 | **0.79** |
| **Escalation Precision (rule layer)** | 0.08 | 0.85 | **0.79** |
| **Escalation Recall (rule layer)** | 1.00 | 0.69 | **0.69** |

### Operational Metrics (Risk & Confidence Engine)
| Metric | Result |
| :--- | :--- |
| **Auto-Handle Rate** | **52.00%** (104 of 200) |
| **Volume False Auto-Handle** | **3.85%** (4 dangerous tweets among 104 auto-handled) |
| **Risk Miss Rate (stricter)** | **25.00%** (4 of 16 true risks auto-handled) |
| **Risk Engine precision (derived)** | ~0.13 (12 of 96 escalations were true risks) |

The Risk Engine is intentionally conservative: it over-escalates (precision ~0.13) to hold the risk miss rate at 25% and volume false auto-handles under 5%. Given the cost matrix (a false auto-handle is far more expensive than a false escalation), this is the correct trade-off for an unsupervised front line.

### Reply Quality (LLM-as-a-Judge on 20 replies)
- Groundedness: 4.70 / 5
- Safety: 5.00 / 5 — caveat: the judge awarded perfect safety even to replies asking users to DM their email; a human pass graded those 4/5. The score reflects a lenient judge, not a proven privacy guarantee.
- Helpfulness: 4.70 / 5

## 4. "What is misleading about my headline number?"
1. **Denominator choice.** The Volume False Auto-Handle rate (3.85%) divides misses by auto-handled volume (4/104). The stricter Risk Miss Rate divides by true risks (4/16 = 25%). I headline the volume number because it reflects the noise human agents would see in production, but the 25% miss rate is the number that should gate deployment.
2. **Self-judging bias.** The judge is the same model as the generator (`openai/gpt-oss-120b`), which inflates groundedness and safety scores. The human agreement study (Spearman on 8 graded baseline-pipeline rows: Groundedness NaN, Safety 0.61, Helpfulness 0.35) quantifies this blind spot.
3. **A substring bug once drove the escalation story.** The first escalation regex matched "sue" inside "issue(s)", producing dozens of false escalations and 0.20 precision. After the word-boundary fix with suffix tolerance, precision is 0.79. My earlier explanation ("the enriched set is hard") was wrong; the bug was the cause. Disclosed because it materially changed the headline.
4. **Golden-set circularity.** The high-risk slice was sampled with keywords that overlap the escalation triggers, so recall on this set overstates production recall.
5. **"Other" skew.** 98 of 200 rows are conversational noise; accuracy is inflated by the dominant class, which is why Macro F1 (0.79) is the number I defend.

## 5. Failure Analysis (Top 5 Modes)
1. **Domain Hallucination:** "how do i DELETE" produced Twitter-style deletion instructions instead of Spotify playlist/account flows.
2. **Context Blindness:** a user stated they already tried the suggested fix; the reply restarted generic troubleshooting.
3. **Hallucinated URL Survival:** the advanced run returned `spotify.com/account/delete/` (the real path is `/account/close/`); the judge still scored groundedness 5/5.
4. **Sarcasm Misclassification:** "HA! Right now you're [URL]" was classified `app_bug` and received a generic reply.
5. **Judge Blindness:** the LLM judge never flagged the hallucinated URLs or domain mismatch above; human review caught all of them.

## 6. What I'd do next with one more week
1. Replace the Risk Engine's keyword layer with a dedicated risk/toxicity LLM classifier, keeping deterministic gates as a backstop.
2. Grounding verifier: check every URL and UI path in drafts against a whitelist extracted from the evidence corpus.
3. Threshold sweep and calibration (temperature scaling) for the 0.7 confidence and 0.4 retrieval gates, replacing the current hand-picked operating points.
4. Re-run the human agreement study on the advanced pipeline's replies (the current study covers 8 graded rows of the baseline pipeline).

## 7. Decision Log (15 Non-Obvious Decisions)
1. Chose SpotifyCares over Amazon/Apple because its public replies contain actionable steps, not just "DM us".
2. Stratified golden-set sampling (100 random / 50 risk / 50 short-vague) to force tail coverage.
3. Headlined Safe Auto-Handle Rate with a <=5% volume false auto-handle target; the 0.7 confidence and 0.4 retrieval gates are chosen operating points, not cited standards (a sweep is next-week work).
4. Pre-LLM PII redaction instead of prompt-level "ignore PII" instructions, for prompt-injection resistance.
5. Dense retrieval over TF-IDF to match "double charged" to "refund" semantics.
6. Trivial baseline = always-"other" + always-escalate, to bound both the accuracy and safety floors.
7. Excluded Banking77 from evaluation to avoid domain shift; used only for taxonomy sanity checks.
8. Chose Groq for zero-cost iteration on the evaluation loop.
9. Manually graded judge outputs and reported the NaN/low Spearman agreement instead of hiding it.
10. Used Macro F1 over accuracy because of the 98/200 "other" skew.
11. Kept escalation as a deterministic policy layer separate from the LLM's JSON so safety rules stay auditable.
12. Adopted word-boundary, suffix-tolerant regexes after the "sue-in-issue" incident; keyword lists are version-controlled in code.
13. Simple baseline = keyword rules (what legacy systems actually run), not TF-IDF + logistic regression.
14. Did not fine-tune: few-shot prompting plus RAG keeps the system auditable and updatable.
15. Report quotes harness output verbatim and discloses single-run variance instead of rounding to flattering numbers.
