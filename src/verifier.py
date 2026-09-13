import re
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s<>"\']+')
TRUSTED_HOSTS = {"t.co", "twitter.com", "x.com"}

def build_url_whitelist(texts):
    paths = set()
    bare_hosts = set()
    for text in texts:
        for url in URL_RE.findall(str(text)):
            parsed = urlparse(url)
            host = parsed.netloc
            path = parsed.path.rstrip('/')
            if not path:
                bare_hosts.add(host)
            else:
                base = f"{parsed.scheme}://{host}{path}"
                paths.add(base)
                paths.add(base + "/")
    return {"paths": paths, "bare_hosts": bare_hosts}

def verify_reply(reply, whitelist):
    urls = URL_RE.findall(str(reply))
    violations = []
    for url in urls:
        parsed = urlparse(url)
        host = parsed.netloc
        if host in TRUSTED_HOSTS:
            continue
        path = parsed.path.rstrip('/')
        base = f"{parsed.scheme}://{host}"
        if not path:
            if host not in whitelist["bare_hosts"]:
                violations.append(url)
        else:
            full_url = f"{base}{path}"
            if full_url not in whitelist["paths"] and (full_url + "/") not in whitelist["paths"]:
                violations.append(url)
    return {"passed": len(violations) == 0, "violations": violations}

def sanitize_reply(reply, violations):
    out = reply
    for v in sorted(violations, key=len, reverse=True):
        out = out.replace(v, "[URL removed: not in historical whitelist]")
    return out
