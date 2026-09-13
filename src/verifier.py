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
                base = f"{parsed.scheme}://{host}"
                paths.add(base)
                paths.add(base + "/")
                current = base
                for part in path.split('/'):
                    if part:
                        current += f"/{part}"
                        paths.add(current)
                        paths.add(current + "/")
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
            if host not in whitelist["bare_hosts"] and base not in whitelist["paths"] and (base + "/") not in whitelist["paths"]:
                violations.append(url)
        else:
            current = base
            found = False
            for part in path.split('/'):
                if part:
                    current += f"/{part}"
                    if current in whitelist["paths"] or (current + "/") in whitelist["paths"]:
                        found = True
                        break
            if not found:
                violations.append(url)
    return {"passed": len(violations) == 0, "violations": violations}

def sanitize_reply(reply, violations):
    out = reply
    for v in violations:
        out = out.replace(v, "[URL removed: not in historical whitelist]")
    return out
