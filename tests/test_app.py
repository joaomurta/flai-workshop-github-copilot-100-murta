"""
Tests for the Mergington High School API.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities dict to original state before each test."""
    original = {
        name: {**data, "participants": list(data["participants"])}
        for name, data in activities.items()
    }
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        data = response.json()
        assert len(data) == 9

    def test_activity_has_required_fields(self, client):
        response = client.get("/activities")
        data = response.json()
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity

    def test_chess_club_is_present(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        email = "newstudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        assert email in activities["Chess Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "test@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup_returns_400(self, client):
        email = "michael@mergington.edu"  # already signed up
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_message_contains_email_and_activity(self, client):
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Drama Club/signup",
            params={"email": email},
        )
        body = response.json()["message"]
        assert email in body
        assert "Drama Club" in body


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self, client):
        email = "michael@mergington.edu"  # pre-existing participant
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/signup", params={"email": email})
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/signup",
            params={"email": "test@mergington.edu"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up_returns_404(self, client):
        email = "notregistered@mergington.edu"
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_unregister_message_contains_email_and_activity(self, client):
        email = "daniel@mergington.edu"
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        body = response.json()["message"]
        assert email in body
        assert "Chess Club" in body
