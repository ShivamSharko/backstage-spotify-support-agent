import httpx
from groq import RateLimitError, NotFoundError
from src.router import ModelRouter

class FakeCompletions:
    def __init__(self, effects):
        self.effects = list(effects)
        self.calls = []
    def create(self, **kwargs):
        self.calls.append(kwargs["model"])
        e = self.effects.pop(0)
        if isinstance(e, Exception):
            raise e
        return e

class OkResp:
    pass

def make_client(effects):
    fc = FakeCompletions(effects)
    class Chat: pass
    class Client: pass
    c = Client()
    c.chat = Chat()
    c.chat.completions = fc
    return c, fc

def err(status, msg):
    req = httpx.Request("POST", "http://x")
    cls = RateLimitError if status == 429 else NotFoundError
    return cls(msg, response=httpx.Response(status, request=req), body=None)

def test_falls_back_on_429():
    r = ModelRouter(api_key="fake")
    c, fc = make_client([err(429, "Rate limit reached, try again in 1s"), OkResp()])
    r.client = c
    r.chat_completion([{"role": "user", "content": "hi"}])
    assert fc.calls == [r.models[0], r.models[1]]
    assert r.usage[r.models[1]] == 1

def test_removes_model_on_404():
    r = ModelRouter(api_key="fake")
    c, fc = make_client([err(404, "model not found"), OkResp()])
    r.client = c
    r.chat_completion([{"role": "user", "content": "hi"}])
    assert r.models[0] in r.removed
    assert fc.calls == [r.models[0], r.models[1]]

