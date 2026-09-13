from src.verifier import build_url_whitelist, verify_reply

def test_hallucinated_spotify_path_flagged():
    wl = build_url_whitelist(["try https://support.spotify.com/close-account/premium-help/ for help"])
    check = verify_reply("go to https://support.spotify.com/close-account/totally-fake-endpoint/", wl)
    assert not check["passed"]
    assert "https://support.spotify.com/close-account/totally-fake-endpoint/" in check["violations"]

def test_known_path_passes():
    wl = build_url_whitelist(["try https://support.spotify.com/close-account/ for help"])
    check = verify_reply("see https://support.spotify.com/close-account/", wl)
    assert check["passed"]

def test_shortener_trusted():
    wl = build_url_whitelist(["nothing"])
    check = verify_reply("see https://t.co/zzz", wl)
    assert check["passed"]

def test_bare_host_does_not_whitelist_paths():
    wl = build_url_whitelist(["visit https://spotify.com for help"])
    check = verify_reply("go to https://spotify.com/account/delete/", wl)
    assert not check["passed"]
