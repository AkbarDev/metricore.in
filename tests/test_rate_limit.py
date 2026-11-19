import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from starlette.requests import Request
from starlette.testclient import TestClient

from app.main import app, get_client_ip, is_trusted_peer, InMemoryRateLimiter, rate_limiter

def make_dummy_request(client_host: str, headers: dict = None) -> Request:
    raw_headers = []
    if headers:
        for k, v in headers.items():
            raw_headers.append((k.lower().encode("latin-1"), v.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "client": (client_host, 12345),
    }
    return Request(scope)

# 1. Peer public IP + spoofed X-Forwarded-For -> returns the peer address
def test_public_peer_ignores_spoofed_x_forwarded_for():
    public_peer = "93.184.216.34"
    req = make_dummy_request(
        client_host=public_peer,
        headers={"X-Forwarded-For": "1.1.1.1, 10.0.0.1"}
    )
    assert not is_trusted_peer(public_peer)
    resolved_ip = get_client_ip(req)
    assert resolved_ip == public_peer

# 2. Peer private IP + "spoofed, real" header -> returns the rightmost value
def test_private_peer_extracts_rightmost_x_forwarded_for():
    private_peer = "10.0.0.1"  # Private IP proxy
    real_ip = "93.184.216.34"
    req = make_dummy_request(
        client_host=private_peer,
        headers={"X-Forwarded-For": f"1.1.1.1, {real_ip}"}
    )
    assert is_trusted_peer(private_peer)
    resolved_ip = get_client_ip(req)
    assert resolved_ip == real_ip

# 3. 100,000 distinct fake keys -> tracked keys never exceed the cap
def test_rate_limiter_key_cap_eviction():
    cap = 1000
    limiter = InMemoryRateLimiter(max_keys=cap, cleanup_interval_seconds=3600, cleanup_call_frequency=1000000)
    for i in range(100000):
        limiter.check_and_record(f"fake_key_{i}", max_requests=10, window_seconds=60)
        if i % 10000 == 0:
            assert len(limiter._requests) <= cap
    assert len(limiter._requests) == cap

# 4. The global backstop returns 429 under a rotating-IP flood & 429 includes Retry-After
def test_global_backstop_rotating_ip_flood_and_retry_after():
    # Configure TestClient with a loopback client host so X-Forwarded-For is trusted
    client = TestClient(app, client=("127.0.0.1", 50000))
    # Reset rate_limiter state for testing
    rate_limiter._requests.clear()

    # Route group /api/autosuggest has global backstop of 600 req/min
    # Let's flood with 600 distinct client IPs through trusted proxy
    for i in range(600):
        fake_ip = f"198.51.{i // 250}.{(i % 250) + 1}"
        resp = client.get(
            "/api/autosuggest?q=a",
            headers={"X-Forwarded-For": fake_ip}
        )
        assert resp.status_code == 200, f"Request {i} failed unexpectedly with {resp.status_code}"

    # Request 601 with a fresh IP should be blocked by the global backstop
    flood_ip = "198.51.250.250"
    blocked_resp = client.get(
        "/api/autosuggest?q=a",
        headers={"X-Forwarded-For": flood_ip}
    )
    assert blocked_resp.status_code == 429
    assert "Retry-After" in blocked_resp.headers
    retry_after = int(blocked_resp.headers["Retry-After"])
    assert retry_after > 0
    assert "Service busy" in blocked_resp.json()["detail"]

# 5. Blocked requests do not append timestamps and 429 includes Retry-After
def test_blocked_requests_retry_after():
    limiter = InMemoryRateLimiter(max_keys=100)
    # Allow 2 requests in 60s
    allowed, _ = limiter.check_and_record("test_key", max_requests=2, window_seconds=60)
    assert allowed is True
    allowed, _ = limiter.check_and_record("test_key", max_requests=2, window_seconds=60)
    assert allowed is True

    # 3rd request should be blocked
    allowed, retry_after = limiter.check_and_record("test_key", max_requests=2, window_seconds=60)
    assert allowed is False
    assert retry_after > 0
    # Deque length should still be exactly 2
    assert len(limiter._requests["test_key"]) == 2
