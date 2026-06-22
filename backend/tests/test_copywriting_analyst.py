import app.models
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import app as fastapi_app
from app.models.post import Post
from app.insights.copywriting_analyst import analyze_post_copywriting


def test_copywriting_heuristics_tone_and_hook():
    # 1. Storytelling / High hook test
    post_story = Post(
        post_url="url-1",
        title="Why I quit my job 5 years ago to build a startup.\n\nIt was a long journey with many lessons learned. I decided to write about it.",
        impressions=1000,
        engagement_rate=0.08
    )
    analysis = analyze_post_copywriting(post_story, median_impressions=500, avg_engagement=0.04)
    assert "quit my job" in analysis["hook"]
    assert analysis["hook_effectiveness"] == "High"  # Starts with "Why I", has numbers
    assert analysis["tone"] == "Storytelling"
    assert any("lessons" in x.lower() or "impressions" in x.lower() for x in analysis["convincing_elements"])

    # 2. Educational / Low hook / Hashtag overload test
    post_edu = Post(
        post_url="url-2",
        title="http://short.url\n\nLearn how to code a backend database API tutorial in python.\n#python #fastapi #sql #db #api #backend #web #dev #coding #programming",
        impressions=100,
        engagement_rate=0.01
    )
    analysis_edu = analyze_post_copywriting(post_edu, median_impressions=500, avg_engagement=0.04)
    assert analysis_edu["hook_effectiveness"] == "Low"  # has link in hook, or too short
    assert analysis_edu["tone"] == "Educational" or analysis_edu["tone"] == "Technical"
    assert any("reduce the number of hashtags" in x.lower() for x in analysis_edu["improvement_suggestions"])
    assert any("move external link" in x.lower() for x in analysis_edu["improvement_suggestions"])


from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite DB for testing FastAPI endpoint
@pytest.fixture(scope="module")
def test_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Pre-populate database with test posts
    db = TestingSessionLocal()
    posts = [
        Post(
            post_url="p1",
            posted_at=datetime(2026, 1, 1, 10, 0),
            post_type="text",
            title="5 tips on how to structure a fastapi project. It helps clean up code.\n#python #fastapi",
            impressions=1000,
            engagement_rate=0.05
        ),
        Post(
            post_url="p2",
            posted_at=datetime(2026, 1, 2, 10, 0),
            post_type="image",
            title="We are excited to announce our new job openings. Join the team today!",
            impressions=500,
            engagement_rate=0.02
        ),
        Post(
            post_url="p3",
            posted_at=datetime(2026, 1, 3, 10, 0),
            post_type="video",
            title="My startup journey: how I failed and learned to build better database systems.\n#startup",
            impressions=200,
            engagement_rate=0.04
        )
    ]
    db.add_all(posts)
    db.commit()
    db.close()

    def override_get_db():
        db_session = TestingSessionLocal()
        try:
            yield db_session
        finally:
            db_session.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def test_api_copywriting_posts_endpoint(test_client):
    # Query all posts (preset=all_time)
    res = test_client.get("/api/copywriting/posts?preset=all_time")
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] == 3
    assert len(data["posts"]) == 3
    
    # Assert fields are present
    p1 = next(p for p in data["posts"] if p["post_url"] == "p1")
    assert p1["hook_effectiveness"] == "High"
    assert p1["tone"] == "Educational" or p1["tone"] == "Technical"

    # Search filter
    res_search = test_client.get("/api/copywriting/posts?preset=all_time&search=excited")
    assert res_search.status_code == 200
    assert res_search.json()["total_count"] == 1
    assert res_search.json()["posts"][0]["post_url"] == "p2"

    # Tone filter
    res_tone = test_client.get("/api/copywriting/posts?preset=all_time&tone=Storytelling")
    assert res_tone.status_code == 200
    assert res_tone.json()["total_count"] == 1
    assert res_tone.json()["posts"][0]["post_url"] == "p3"

    # Performance tier filter (top 25%, mid, bottom 25% of 3 items)
    # reach sorted: p1 (1000) -> top, p2 (500) -> mid, p3 (200) -> low
    res_top = test_client.get("/api/copywriting/posts?preset=all_time&performance_tier=top")
    assert res_top.status_code == 200
    assert res_top.json()["total_count"] == 1
    assert res_top.json()["posts"][0]["post_url"] == "p1"

    # Sorting by impressions desc
    res_sort = test_client.get("/api/copywriting/posts?preset=all_time&sort_by=impressions&sort_order=desc")
    assert res_sort.status_code == 200
    posts = res_sort.json()["posts"]
    assert posts[0]["impressions"] == 1000
    assert posts[1]["impressions"] == 500
    assert posts[2]["impressions"] == 200
