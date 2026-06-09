"""
Tests for the Mergington High School Activities API.
Each test follows the AAA (Arrange-Act-Assert) pattern.
"""
import pytest
from fastapi.testclient import TestClient

class TestGetActivities:
    """Tests for retrieving activities."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that all activities are returned with correct structure."""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert all(activity in data for activity in expected_activities)
        assert data["Chess Club"]["max_participants"] == 12
        assert len(data["Chess Club"]["participants"]) == 2

    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that each activity contains required fields."""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert all(field in activity_data for field in required_fields)

class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html."""
        # Arrange
        expected_redirect_url = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url

class TestSignup:
    """Tests for the signup endpoint."""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """Test successfully signing up a new participant."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert new_email in activities[activity_name]["participants"]

    def test_signup_duplicate_participant_rejected(self, client, reset_activities):
        """Test that duplicate signups are rejected."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signing up increases the participant count."""
        # Arrange
        activity_name = "Programming Class"
        new_email = "count_test@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count + 1

class TestUnregister:
    """Tests for the unregister endpoint."""
    
    def test_unregister_existing_participant_success(self, client, reset_activities):
        """Test successfully unregistering an existing participant."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify participant was removed
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count - 1
        assert email_to_remove not in updated_activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """Test that unregistering non-existent participant returns 404."""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from non-existent activity returns 404."""
        # Arrange
        nonexistent_activity = "Nonexistent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_decreases_participant_count(self, client, reset_activities):
        """Test that unregistering decreases the participant count."""
        # Arrange
        activity_name = "Gym Class"
        email_to_remove = "john@mergington.edu"
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity_name]["participants"])
        
        # Act
        client.delete(f"/activities/{activity_name}/unregister?email={email_to_remove}")
        
        # Assert
        updated_activities = client.get("/activities").json()
        updated_count = len(updated_activities[activity_name]["participants"])
        assert updated_count == initial_count - 1

class TestIntegration:
    """Integration tests for signup and unregister workflows."""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test complete workflow: signup new participant, then unregister."""
        # Arrange
        activity_name = "Programming Class"
        new_email = "workflow@mergington.edu"
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        assert signup_response.status_code == 200
        
        # Assert - Participant added
        activities_after_signup = client.get("/activities").json()
        assert new_email in activities_after_signup[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={new_email}"
        )
        assert unregister_response.status_code == 200
        
        # Assert - Participant removed
        activities_after_unregister = client.get("/activities").json()
        assert new_email not in activities_after_unregister[activity_name]["participants"]
