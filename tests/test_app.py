import pytest


@pytest.mark.parametrize("follow_redirects", [False])
def test_root_redirects_to_static_index(client, follow_redirects):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=follow_redirects)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 9
    assert activities[expected_activity]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]
    assert activities[expected_activity]["max_participants"] == 12


def test_signup_adds_participant(client, activities_state):
    # Arrange
    activity = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities_state[activity]["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity(client, activities_state):
    # Arrange
    activity = "Art Club"
    activities_state[activity]["participants"] = [
        f"student-{number}@mergington.edu" for number in range(15)
    ]

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": "new@mergington.edu"}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_signup_requires_email(client):
    # Arrange
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup")

    # Assert
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]


def test_unregister_removes_participant(client, activities_state):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in activities_state[activity]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity = "Robotics Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_unregister_and_resignup_workflow(client, activities_state):
    # Arrange
    activity = "Soccer Club"
    email = "student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )
    unregister_response = client.delete(f"/activities/{activity}/participants/{email}")
    resignup_response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert resignup_response.status_code == 200
    assert activities_state[activity]["participants"] == [email]
