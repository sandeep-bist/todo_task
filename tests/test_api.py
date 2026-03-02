import pytest
from rest_framework.test import APIClient
from tasks.utils import init_database

@pytest.fixture(autouse=True)
def setup_db():
    init_database()

@pytest.mark.django_db
def test_create_and_list_task():
    client = APIClient()
    response = client.post('/api/tasks/', {
        "title": "Test Task",
        "description": "Do something",
        "due_date": "2026-03-15",
        "status": "pending"
    })
    assert response.status_code == 201
    assert response.data["title"] == "Test Task"

    list_response = client.get('/api/tasks/')
    assert list_response.status_code == 200
    assert len(list_response.data) >= 1