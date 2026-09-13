import time
import re
from groq import Groq, RateLimitError, NotFoundError, APIStatusError


class ModelRouter:
    """Self-healing fallback router across Groq free-tier models (March 2026 limits)."""

    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        # Ordered by quality, verified against the March 2026 console table
        self.models = [
            "openai/gpt-oss-120b",   # Best reasoning + JSON (1K RPD / 200K TPD)
            "qwen/qwen3.8-27b",      # Strong 27B fallback (1K RPD / 200K TPD)
            "openai/gpt-oss-20b",    # Same family, separate budget (1K RPD / 200K TPD)
            "allam-2-7b",            # Workhorse: 7K RPD / 500K TPD
            "groq/compound-mini",    # Last resort: 70K TPM, no TPD cap (250 RPD)
        ]
        self.cooldowns = {m: 0.0 for m in self.models}
        self.removed = set()
        self.usage = {m: 0 for m in self.models}

    def chat_completion(self, messages, response_format=None, temperature=0.0):
        now = time.time()
        for model in self.models:
            if model in self.removed or now < self.cooldowns[model]:
                continue
            kwargs = {"model": model, "messages": messages, "temperature": temperature}
            if response_format:
                kwargs["response_format"] = response_format
            try:
                time.sleep(0.1)
                resp = self.client.chat.completions.create(**kwargs)
                self.usage[model] += 1
                return resp
            except RateLimitError as e:
                wait = self._cooldown_seconds(str(e))
                print(f"  ⚠️ 429 on {model}. Cooling down {wait:.0f}s, switching...")
                self.cooldowns[model] = time.time() + wait
            except NotFoundError:
                print(f"  🚫 404 on {model}: not available on this account. Removed from pool.")
                self.removed.add(model)
            except APIStatusError as e:
                status = getattr(e, "status_code", 500)
                if status in (400, 401, 403):
                    print(f"  🚫 {status} on {model}. Removed from pool.")
                    self.removed.add(model)
                else:
                    print(f"  ⚠️ {status} on {model}. Cooling down 30s, switching...")
                    self.cooldowns[model] = time.time() + 30
            except Exception:
                print(f"  ⚠️ Unexpected error on {model}. Cooling down 15s, switching...")
                self.cooldowns[model] = time.time() + 15
        raise Exception("All models in router exhausted (rate-limited or unavailable).")

    @staticmethod
    def _cooldown_seconds(error_str):
        low = error_str.lower()
        if "tokens per day" in low or "requests per day" in low:
            return 6 * 3600  # daily budget gone - do not retry today
        m = re.search(r"try again in (?:(\d+)m)?(\d+\.?\d*)s", low)
        if m:
            mins = int(m.group(1)) if m.group(1) else 0
            return mins * 60 + float(m.group(2)) + 5
        return 60

    def summary(self):
        return {m: c for m, c in self.usage.items() if c > 0}
