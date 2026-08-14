from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_root():

    response = client.get("/")

    assert response.status_code == 200


def test_schedule_endpoint():

    response = client.post(
        "/schedule",
        json={
            "student_id": "671234",
            "target_credits": 18,
            "allow_early": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["total_credits"] == 18


def test_unknown_student_returns_404():

    response = client.post(
        "/schedule",
        json={
            "student_id": "999999",
            "target_credits": 18,
            "allow_early": True,
        },
    )

    assert response.status_code == 404


def test_credit_below_minimum_returns_422():

    response = client.post(
        "/schedule",
        json={
            "student_id": "671234",
            "target_credits": 10,
            "allow_early": True,
        },
    )

    assert response.status_code == 422


def test_credit_above_maximum_returns_422():

    response = client.post(
        "/schedule",
        json={
            "student_id": "671234",
            "target_credits": 30,
            "allow_early": True,
        },
    )

    assert response.status_code == 422