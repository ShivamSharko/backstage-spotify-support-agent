# Backstage: Customer Support Agent — Hiver Take-Home Assignment

## 1. Problem Framing
**Brand chosen:** Spotify (SpotifyCares).
**Why:** Spotify has high volume (~43k support replies), clear digital intents (billing, app bugs, account access), and historically provides actionable troubleshooting steps in public tweets rather than just saying "DM us".

**What "good" means:**
A "good" agent is safe, grounded, and operationally useful. It should correctly triage intents, retrieve historical evidence, and draft replies that do not hallucinate fake Spotify URLs or policies. Most importantly, it must escalate high-risk issues (hacks, fraud, legal threats) without overwhelming human agents with false alarms.

**What I chose not to build:**
I did not build a live Twitter integration, a multi-turn conversation state manager, or actual account-action execution (e.g., actually processing a refund). The scope was strictly classification, grounded drafting, and escalation decisions based on historical data.

## 2. System Design & Baselines
**Main System:**
1. **Intent Classifier:** Groq LLM (`openai/gpt-oss-120b`) with JSON structured output.
2. **Retrieval:** TF-IDF + Cosine Similarity over 43,000 historical Spotify replies.
3. **Drafting:** LLM prompted with the classified intent and top-3 retrieved historical examples.
4. **Escalation:** Rule-based keyword trigger (e.g., "hack", "fraud", "sue").

**Baselines:**
- **Trivial Baseline:** Majority class classifier (`other`) + canned "Please DM us" reply + Always Escalate.
- **Simple Baseline:** TF-IDF keyword matching for intent + nearest-neighbor historical reply.

## 3. Results on Golden Set (200 Hand-Labelled Examples)

| Metric | Main System (LLM + TF-IDF) | Simple Baseline (Rules) |
| :--- | :--- | :--- |
| **Intent Accuracy** | 86% | ~40% (estimated) |
| **Intent Macro F1** | 0.84 | ~0.25 |
| **Escalation Precision** | 0.20 | 0.05 |
| **Escalation Recall** | 0.56 | 0.10 |
| **Judge Groundedness** | 4.95 / 5 | N/A |
| **Judge Safety** | 4.55 / 5 | N/A |

**Headline Number:** 86% Intent Accuracy and 4.95/5 Groundedness Score.

## 4. "What is misleading about my headline number?"
The headline number is highly misleading for three reasons:
1. **The LLM Judge is biased and blind to hallucinations.** When I manually graded 10 replies against the LLM Judge, the Human-Judge Spearman correlation for "Groundedness" was `NaN`. This occurred because the LLM Judge gave almost every reply a 5/5, failing to catch severe domain hallucinations.
2. **High "Other" intent skew.** 98 out of 200 tweets in the golden set were conversational noise ("thanks", "DM sent"), which are easy to classify. The Macro F1 (0.84) is a better metric than Accuracy, but it still hides struggles with rare intents.
3. **Escalation rules are brittle.** A 20% precision means 80% of escalated tweets were false alarms. In production, this would annoy human agents and defeat the purpose of automation.

## 5. Failure Analysis (Top 5 Modes)
1. **Domain Hallucination:** *Example (Row 9)* User asks "how do i DELETE". The AI confidently explains how to delete a *Tweet* (Twitter UI) instead of a *Song/Playlist* (Spotify UI). The Judge gave this a 5/5.
2. **Context Blindness:** *Example (Row 8)* User states they already tried a test account and it worked. The AI ignores this context and spits out generic "log out and clear cache" troubleshooting steps.
3. **URL Hallucination:** *Example (Rows 2 & 10)* The AI invents URLs like `spotify.com/password-reset` and presents them as fact. 
4. **Intent Ambiguity:** The model struggles to distinguish between a broken feature (`app_bug`) and a missing feature (`feature_request`), resulting in 55% precision for feature requests.
5. **Escalation False Positives:** The rule-based escalation triggers on standard frustration (e.g., "this is so annoying") rather than true risk, tanking precision.

## 6. What I'd do next with one more week
1. **Replace TF-IDF with Dense Retrieval:** Use sentence-transformers to capture semantic meaning (e.g., matching "charged twice" to "refund" even if the words don't overlap).
2. **LLM-based Escalation:** Replace brittle keyword rules with a secondary LLM classifier specifically prompted to evaluate risk and toxicity, improving precision.
3. **Strict Grounding Constraints:** Implement a verifier that checks if all URLs and UI steps in the generated reply actually exist in the retrieved evidence or a predefined Spotify API tool.

## 7. Decision Log
- Chose SpotifyCares due to high volume of actionable, public troubleshooting replies.
- Used a time-based/stratified sample for the Golden Set (Random + High-Risk + Short/Hard) to ensure tail events were evaluated.
- Chose Groq for fast, cost-free inference during the iterative evaluation loop.
- Used Macro F1 instead of Accuracy to penalize the model if it just guessed the majority class ("other").
- Kept escalation as a separate rules-engine step rather than bundling it into the LLM intent prompt, to ensure deterministic safety triggers.
- Manually graded 10 replies to prove the LLM-as-a-Judge was flawed (correlation = NaN), which is a crucial finding for production AI safety.

