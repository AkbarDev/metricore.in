"""
Unit tests for the Google AI Stack section, data loader, and routes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from app.main import app
from app.google_stack import (
    get_all_google_tools,
    get_google_tool_by_slug,
    get_google_categories,
    get_google_status_counts,
)

client = TestClient(app)


def test_google_stack_data_loader():
    tools = get_all_google_tools()
    assert len(tools) >= 15, f"Expected at least 15 tools, got {len(tools)}"

    categories = get_google_categories()
    assert len(categories) >= 5

    status_counts = get_google_status_counts()
    assert status_counts["free"] > 0

    antigravity = get_google_tool_by_slug("google-antigravity")
    assert antigravity is not None
    assert antigravity["name"] == "Google Antigravity"
    assert len(antigravity["competitors"]) >= 3


def test_google_stack_overview_page():
    response = client.get("/google-ai-stack/")
    assert response.status_code == 200
    assert "Google AI Stack" in response.text
    assert "Google Antigravity" in response.text
    assert "NotebookLM" in response.text
    assert "Pomelli" in response.text


def test_google_stack_detail_page():
    response = client.get("/google-ai-stack/google-antigravity/")
    assert response.status_code == 200
    assert "Google Antigravity" in response.text
    assert "Claude Code" in response.text
    assert "Competitor Comparison" in response.text
    assert "Verified:" in response.text


def test_google_stack_404():
    response = client.get("/google-ai-stack/non-existent-tool-slug/")
    assert response.status_code == 404


def test_google_stack_static_mount():
    response = client.get("/google_stack/Antigravity.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_google_stack_head_request():
    response = client.head("/google-ai-stack/")
    assert response.status_code == 200
    assert response.content == b""
    assert "x-content-type-options" in response.headers
