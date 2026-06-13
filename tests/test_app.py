"""
Tests for the Mergington High School Activities API.

Uses pytest with FastAPI's TestClient for synchronous HTTP testing.
Fixtures reset the in-memory activities state between tests to ensure isolation.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Save and restore the in-memory activities dict before and after each test.
    This ensures tests don't interfere with each other.
    """
    original = copy.deepcopy(activities)
    yield
    # Restore original state after test
    activities.clear()
    activities.update(original)


class TestActivities:
    """Tests for the /activities endpoint."""

    def test_get_activities(self, client, reset_activities):
        """GET /activities returns all activities with expected structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        # Verify a known activity exists
        assert "Chess Club" in data
        # Verify activity structure
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    """Tests for the /signup endpoint."""

    def test_signup_success(self, client, reset_activities):
        """POST /activities/{name}/signup with valid email registers participant."""
        activity = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up new participant
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]

    def test_signup_duplicate(self, client, reset_activities):
        """POST /signup twice with same email returns 400."""
        activity = "Chess Club"
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Second signup should fail
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    def test_signup_activity_not_found(self, client, reset_activities):
        """POST /activities/{invalid}/signup returns 404."""
        response = client.post(
            "/activities/NonexistentClub/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_full(self, client, reset_activities):
        """POST /signup to full activity returns 400."""
        activity = "Chess Club"
        # Get the activity and fill it to capacity
        activities[activity]["participants"] = [
            f"student{i}@mergington.edu" for i in range(activities[activity]["max_participants"])
        ]
        
        # Try to sign up when full
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()


class TestUnregister:
    """Tests for the /participants DELETE endpoint."""

    def test_unregister_success(self, client, reset_activities):
        """DELETE /activities/{name}/participants removes participant."""
        activity = "Chess Club"
        email = activities[activity]["participants"][0]  # Get an existing participant
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        initial_count = len(response.json()[activity]["participants"])
        
        # Remove participant
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "unregistered" in data["message"].lower()
        
        # Verify participant was removed
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()[activity]["participants"]

    def test_unregister_not_found(self, client, reset_activities):
        """DELETE with nonexistent participant returns 404."""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_unregister_activity_not_found(self, client, reset_activities):
        """DELETE from nonexistent activity returns 404."""
        response = client.delete(
            "/activities/NonexistentClub/participants",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestIntegration:
    """Integration tests combining multiple endpoints."""

    def test_signup_and_unregister_flow(self, client, reset_activities):
        """Test full flow: signup → verify → unregister → verify removed."""
        activity = "Programming Class"
        email = "integration@mergington.edu"
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/participants",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_activity_availability_updates(self, client, reset_activities):
        """Test that availability spot count updates correctly."""
        activity = "Gym Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Get initial availability
        response = client.get("/activities")
        activity_data = response.json()[activity]
        initial_spots = activity_data["max_participants"] - len(activity_data["participants"])
        
        # Sign up first student
        client.post(f"/activities/{activity}/signup", params={"email": email1})
        response = client.get("/activities")
        spots_after_1 = response.json()[activity]["max_participants"] - len(response.json()[activity]["participants"])
        assert spots_after_1 == initial_spots - 1
        
        # Sign up second student
        client.post(f"/activities/{activity}/signup", params={"email": email2})
        response = client.get("/activities")
        spots_after_2 = response.json()[activity]["max_participants"] - len(response.json()[activity]["participants"])
        assert spots_after_2 == initial_spots - 2
        
        # Unregister first student
        client.delete(f"/activities/{activity}/participants", params={"email": email1})
        response = client.get("/activities")
        spots_after_unregister = response.json()[activity]["max_participants"] - len(response.json()[activity]["participants"])
        assert spots_after_unregister == initial_spots - 1
