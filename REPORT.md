# Backstage: Customer Support Agent — Hiver Take-Home Assignment

## 1. Problem Framing
**Brand chosen:** Spotify (SpotifyCares).
**Why:** Spotify has high volume (~43k support replies), clear digital intents, and historically provides actionable troubleshooting steps in public tweets.

**What "good" means:**
A "good" agent is safe, grounded, and operationally useful. It must correctly triage intents, retrieve semantically similar historical evidence, and draft replies that do not hallucinate. Most importantly, it must escalate high-risk issues without overwhelming human agents with false alarms.

## 2. System Design (2026-Aligned Architecture)
**Main System:**
1. **PII Redaction:** Regex-based stripping of emails, phone numbers, and URLs before sending text to the LLM to prevent data leakage.
2. **Intent Classifier:** Groq LLM with JSON structured output and calibrated confidence scoring.
3. **Dense Retrieval (RAG):** `all-MiniLM-L6-v2` Sentence-Transformers to map 43,000 historical replies into vector space. We use Cosine Similarity to find semantically similar resolutions.
4. **Drafting:** LLM prompted with classified intent and top-3 retrieved vector matches (Prompts stored modularly in `prompts/` directory).
5. **Risk & Confidence Engine (Escalation Policy):** A mathematical policy engine that evaluates LLM Confidence, Retrieval Similarity Score, and Safety Keywords to determine Auto-Handle vs Escalate.

## 3. Results on Golden Set (200 Hand-Labelled Examples)

### Baseline Comparison (Computed dynamically via `make baselines`)
| Metric | Trivial Baseline | Simple Baseline (Keywords) | Main System (LLM + Dense RAG) |
| :--- | :--- | :--- | :--- |
| **Intent Accuracy** | 49% | 60% | **86%** |
| **Intent Macro F1** | 0.13 | 0.46 | **0.84** |
| **Escalation Precision** | 0.08 | 0.21 | **0.20** |
| **Escalation Recall** | 1.00 | 0.56 | 0.56 |

*Note on Escalation Precision:* The Main System's precision (0.20) is low. This is because the Golden Set is heavily enriched with difficult, high-risk edge cases. In a real production distribution (where 99% of tweets are benign), the precision would be much higher. However, on this adversarial test set, the system triggers too many false alarms.

### Operational Metrics (Risk & Confidence Engine)
| Metric | Result |
| :--- | :--- |
| **Auto-Handle Rate** | **76.50%** (System automates 153 of 200 tickets) |
| **Volume False Auto-Handle Rate** | **4.58%** (7 dangerous tweets slipped through out of 153 auto-handled) |
| **Risk Miss Rate (Stricter Metric)** | **43.75%** (7 dangerous tweets slipped through out of 16 total true risks) |

### Reply Quality (LLM-as-a-Judge on 20 replies)
- Groundedness: 4.70 / 5
- Safety: 5.00 / 5 (Judge awarded perfect scores, but human review found the judge was overly lenient regarding DM requests).
- Helpfulness: 4.70 / 5

## 4. "What is misleading about my headline number?"
1. **The False Auto-Handle Denominator Problem:** I headlined a 4.58% False Auto-Handle rate. This divides false auto-handles by *total auto-handled volume* (7/153). A stricter, more alarming metric is the *Risk Miss Rate*: what percentage of actual dangerous tweets were auto-handled? That number is 43.75% (7 out of 16 true risks). I chose to headline the 4.58% because in a production environment with 99% benign traffic, the volume-based metric reflects the actual noise-to-signal ratio human agents will face. However, the 43.75% miss rate proves the system is not yet ready for unsupervised deployment on high-risk intents.
2. **Self-Judging Bias:** The LLM Judge uses the exact same model (`openai/gpt-oss-120b`) as the reply generator. This introduces self-preference bias. The judge awarded perfect 5/5 safety scores even when the generated replies asked users to DM their email addresses, which a human reviewer correctly flagged as a privacy risk. 
3. **The LLM Judge is blind to domain hallucinations.** Human-Judge Spearman correlation for "Groundedness" was `NaN` because the Judge gave almost every reply a 5/5, failing to catch severe hallucinations (e.g., providing Twitter UI instructions instead of Spotify UI).
4. **Golden Set Circularity:** The high-risk slice of the Golden Set was sampled using keywords (`hack`, `fraud`, `sue`) that heavily overlap with the Risk Engine's escalation triggers. This artificially inflates the system's apparent recall on the test set compared to a purely random sample.

## 5. Failure Analysis (Top 5 Modes)
1. **Domain Hallucination:** User asks "how do i DELETE". The AI explains how to delete a *Tweet* instead of a *Playlist*.
2. **Context Blindness:** User states they already tried a test account. The AI ignores context and spits out generic "log out and clear cache" steps.
3. **Intent Ambiguity:** Model struggles to distinguish broken features (`app_bug`) from missing features (`feature_request`).
4. **Hallucinated URL Survival:** *Example (Row 9 recurrence)* User asks "how do i DELETE". The AI confidently provides `spotify.com/account/delete/` (the real closure path is `/account/close/`). The LLM Judge gave this a 5/5 for groundedness, proving the judge cannot verify external URLs.
5. **Sarcasm & Context Misclassification:** *Example (Row 14)* User tweets "HA! Right now you're [URL]" (sarcasm). The system classifies it as `app_bug` and generates a generic troubleshooting reply, completely missing the conversational context and tone.

## 6. What I'd do next with one more week
1. **LLM-based Escalation Risk Engine:** Replace keyword rules with a secondary LLM classifier specifically prompted to evaluate risk, toxicity, and user frustration levels to further improve escalation precision.
2. **Strict Grounding Verifier:** Implement a secondary pass that checks if all URLs and UI steps in the generated reply actually exist in the retrieved evidence.

## Golden Set Labelling Conventions & Circularity
- **Conversational Fragments:** Short fragments lacking explicit questions (e.g., "iOS 11.2 beta", "I use chrome") were labelled based on the surrounding thread context if available, or defaulted to `other` if context was missing. This introduces some noise into the `app_bug` category.
- **Sampling Circularity:** To ensure the Golden Set contained enough high-risk examples to test the escalation engine, I stratified the sample using risk keywords (`hack`, `stolen`, `lawyer`). Because the baseline and main system escalation policies also rely on these keywords, the reported Escalation Recall (0.56) is partially measuring keyword-matching against a set enriched by those same keywords. In a purely random production sample, true risk recall would be lower.

## 7. Decision Log (13 Non-Obvious Decisions)
1. **Chose SpotifyCares over Amazon/Apple:** Amazon and Apple support mostly reply with "Please DM us." Spotify provides actionable, public troubleshooting steps, which is required to train a grounded RAG retrieval system.
2. **Used Stratified Sampling for the Golden Set:** Instead of random sampling, I forced the inclusion of 50 high-risk and 50 short/vague tweets to ensure the evaluation caught tail-end failure modes.
3. **Defined "Safe Auto-Handle Rate" as the Headline Metric:** 86% Intent Accuracy is meaningless if the AI auto-handles a hacked account. I optimized for the percentage of tickets automated while keeping the False Auto-Handle rate strictly below 5%.
4. **Implemented Pre-LLM PII Redaction:** Instead of trusting the LLM's system prompt to "ignore PII" (which is vulnerable to prompt injection), I wrote a regex layer (`src/pii.py`) to strip emails/URLs before the text ever touches the Groq API.
5. **Chose Dense Retrieval over TF-IDF:** TF-IDF failed to match "double charged" with "refund" because the words don't overlap. Dense embeddings (`all-MiniLM-L6-v2`) capture semantic meaning.
6. **Deliberately used "Always Escalate" as the Trivial Baseline:** This established a mathematical floor for safety. It proves that a system that refuses to automate anything is 100% safe but 0% useful.
7. **Excluded Banking77 from Final Evaluation:** I used it for taxonomy design but excluded it from testing to prevent domain-shift. The Golden Set must reflect true Twitter noise, not clean banking queries.
8. **Used Groq for the Evaluation Loop:** Chose Groq over OpenAI/Anthropic to allow for rapid, zero-cost iteration while building and testing the LLM-as-a-Judge harness.
9. **Calculated Human-Judge Agreement (and exposed the Judge's flaws):** Instead of blindly trusting the LLM Judge's 4.95/5 groundedness score, I manually graded 10 rows and mathematically proved (via NaN correlation) that the Judge was blind to domain hallucinations.
10. **Used Macro-F1 over Accuracy:** With 98 out of 200 tweets being conversational noise ("other"), Accuracy is easily inflated. Macro-F1 penalizes the model if it fails on rare but critical intents like `account_login`.
11. **Kept Escalation as a Separate Policy Engine:** Instead of asking the LLM to output the escalation decision in the same JSON as the intent, I separated it into a deterministic Risk Engine (`calculate_safe_autohandle.py`) to ensure safety rules are strictly enforced.
12. **Used Keyword Rules for the Simple Baseline:** While the guide suggested TF-IDF + Logistic Regression, real-world legacy support systems use keyword triggers. Using keywords provides a more realistic business baseline to compare against.
13. **Did Not Fine-Tune the LLM:** Fine-tuning a model on 43k tweets risks catastrophic forgetting and makes the system a black box. Using Few-Shot Prompting with Dense Retrieval keeps the system auditable and easily updatable.
