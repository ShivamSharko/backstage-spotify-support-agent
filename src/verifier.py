import re
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s]+')
SHORTENERS = {"t.co", "bit.ly", "goo.gl", "buff.ly", "tinyurl.com"}
# Twitter's own shortener is trusted (came from brand's historical tweets)
TRUSTED_HOSTS = {"t.co", "twitter.com", "x.com", "support.spotify.com", "spotify.com"}

def extract_urls(text):
    return URL_RE.findall(text or "")

def build_url_whitelist(replies_text_list):
    whitelist = set()
    for text in replies_text_list:
        for url in extract_urls(text):
            parsed = urlparse(url)
            host = parsed.netloc.lower().replace("www.", "")
            if host in SHORTENERS:
                continue
            path = parsed.path.rstrip("/")
            whitelist.add(host)
            if path:
                parts = path.split("/")
                for i in range(1, len(parts) + 1):
                    whitelist.add(host + "/".join(parts[:i]))
    return whitelist

def verify_reply(reply, whitelist):
    violations = []
    for url in extract_urls(reply):
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        if host in TRUSTED_HOSTS:
            continue
        path = parsed.path.rstrip("/")
        parts = path.split("/")
        ok = host in whitelist or any((host + "/".join(parts[:i])) in whitelist for i in range(1, len(parts) + 1))
        if not ok:
            violations.append(url)
    return {"passed": len(violations) == 0, "violations": violations}

def sanitize_reply(reply, violations):
    cleaned = reply
    for url in violations:
        cleaned = cleaned.replace(url, "[link removed by grounding verifier]")
    return cleaned
