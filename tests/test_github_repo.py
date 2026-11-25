import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from app.main import app
from app.github_repo import get_all_github_repos, get_featured_github_repos

client = TestClient(app)


def test_github_repo_data_loader():
    repos = get_all_github_repos()
    assert len(repos) == 8
    featured = get_featured_github_repos()
    assert 3 <= len(featured) <= 5
    for r in repos:
        assert r.get("name")
        assert r.get("slug")
        assert r.get("description")
        assert r.get("why_useful")
        assert r.get("last_verified")


def test_github_repo_overview_page():
    response = client.get("/github-repo/")
    assert response.status_code == 200
    html = response.text
    assert "GitHub Repos" in html
    assert "agency-agents" in html
    assert "Agent-Reach" in html
    assert "shepherd" in html
    assert "Open-LLM-VTuber" in html
    assert "agentic-inbox" in html
    assert "Voicebox" in html
    assert "LibreChat" in html
    assert "open-higgsfield-ai" in html
    # Ensure no reference screenshots are embedded inside the UI cards
    grid_html = html.split('<main id="github-repos-grid"')[1].split("</main>")[0]
    assert "<img" not in grid_html
    assert "agency_agents.png" not in grid_html
    assert "Agents_reach.png" not in grid_html
    # Ensure no competitor comparison content
    assert "competitor_matrix" not in html
    assert "Free Competitor Equivalents" not in html


def test_github_repo_head_request():
    response = client.head("/github-repo/")
    assert response.status_code == 200
    assert response.text == ""
