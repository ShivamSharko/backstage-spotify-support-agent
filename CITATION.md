# Citations & References

This project builds upon several foundational concepts in modern NLP and AI evaluation:

## Retrieval-Augmented Generation (RAG)
- Lewis, P., et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." *NeurIPS*. (Foundational architecture for our Dense Retrieval module).
- Asai, A., et al. (2023). "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection." (Inspiration for grounding constraints).

## LLM-as-a-Judge & Evaluation
- Zheng, L., et al. (2023). "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." *NeurIPS*. (Foundational rubric design for our evaluation harness).
- Liu, Y., et al. (2023). "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment." (Inspiration for our JSON-structured judge prompts).

## Datasets
- Kaggle: "Customer Support on Twitter" (thoughtvector).
- PolyAI: "Banking77" dataset. *(Note: Banking77 was evaluated during the intent taxonomy design phase to map generic financial intents to brand-specific intents, but was excluded from final evaluation to prevent domain-shift and ensure the Golden Set reflected true Twitter support noise).*

## Uncertainty & Safety
- Kadavath, S., et al. (2022). "Language Models (Mostly) Know What They Know." (Inspiration for using verbalized LLM confidence in our Risk & Confidence Engine).

