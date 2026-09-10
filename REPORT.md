# Backstage: Customer Support Agent — Hiver Take-Home Assignment

## 1. Problem Framing
**Brand chosen:** Spotify (SpotifyCares).
**Why:** Spotify has high volume (~43k support replies), clear digital intents, and historically provides actionable troubleshooting steps in public tweets.

**What "good" means:**
A "good" agent is safe, grounded, and operationally useful. It must correctly triage intents, retrieve semantically similar historical evidence, and draft replies that do not hallucinate. Most importantly, it must escalate high-risk issues without overwhelming human agents with false alarms.

## 2. System Design (2026-Aligned Architecture)
**Main System:**
1. **PII Redaction:** Regex-based stripping of emails, phone numbers, and URLs before sending text to the LLM to prevent data leakage.
2. **Intent Classifier:** Groq LLM (`openai/gpt-oss-120b`) with JSON structured output.
3. **Dense Retrieval:** `all-MiniLM-L6-v2` Sentence-Transformers to map 43,000 historical replies into vector space. We use Cosine Similarity to find semantically similar resolutions (e.g., matching "double charged" to "refund" without keyword overlap).
4. **Drafting:** LLM prompted with classified intent and top-3 retrieved vector matches.
5. **Escalation:** Rule-based keyword trigger for high-risk terms (hack, fraud, sue).

## 3. Results on Golden Set (200 Hand-Labelled Examples)

| Metric | Trivial Baseline | Simple Baseline (Keywords) | Main System (LLM + Dense RAG) |
| :--- | :--- | :--- | :--- |
| **Intent Accuracy** | 49% | 60% | **86%** |
| **Intent Macro F1** | 0.13 | 0.46 | **0.84** |
| **Escalation Precision** | 0.08 | 0.21 | 0.20 |
| **Escalation Recall** | 1.00 | 0.56 | 0.56 |

**Reply Quality (LLM-as-a-Judge on 20 replies):**
- Groundedness: 4.70 / 5
- Safety: 5.00 / 5 (Perfect score due to PII Redaction layer)
- Helpfulness: 4.70 / 5

## 4. "What is misleading about my headline number?"
1. **The LLM Judge is biased.** Human-Judge Spearman correlation for "Groundedness" was `NaN` because the Judge gave almost every reply a 5/5, failing to catch domain hallucinations (e.g., Twitter UI vs Spotify UI).
2. **Escalation rules are brittle.** A 20% precision means 80% of escalated tweets were false alarms. In production, this would annoy human agents.
3. **High "Other" intent skew.** 98 out of 200 tweets were conversational noise, artificially inflating accuracy metrics. Macro F1 (0.84) is the true measure of success.

## 5. Failure Analysis (Top 3 Modes)
1. **Domain Hallucination:** User asks "how do i DELETE". The AI explains how to delete a *Tweet* instead of a *Playlist*.
2. **Context Blindness:** User states they already tried a test account. The AI ignores context and spits out generic "log out and clear cache" steps.
3. **Intent Ambiguity:** Model struggles to distinguish broken features (`app_bug`) from missing features (`feature_request`).

## 6. What I'd do next with one more week
1. **LLM-based Escalation Risk Engine:** Replace keyword rules with a secondary LLM classifier specifically prompted to evaluate risk, toxicity, and user frustration levels to improve escalation precision.
2. **Strict Grounding Verifier:** Implement a secondary pass that checks if all URLs and UI steps in the generated reply actually exist in the retrieved evidence.

## 7. Decision Log
- Chose Dense Retrieval (Sentence-Transformers) over TF-IDF to capture semantic meaning.
- Added a PII Redaction layer to ensure user privacy before LLM inference, which bumped Safety scores to 5.00/5.
- Used Macro F1 instead of Accuracy to penalize the model for guessing the majority class.
- Manually graded 10 replies to mathematically prove the LLM-as-a-Judge was flawed (correlation = NaN).
