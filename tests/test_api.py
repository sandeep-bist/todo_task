

# tests/test_api.py
import pytest
from rest_framework import status
from task.views import get_task_by_id,get_all_tasks,delete_task
from datetime import date

# ────────────────────────────────────────────────
# GET /api/tasks/  → List all tasks
# ────────────────────────────────────────────────

def test_list_tasks_empty(api_client):
    print(api_client,"--------------")
    """GET /api/tasks/ should return empty list when no tasks exist"""
    response = api_client.get('/api/tasks/')
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) == 0


def test_list_tasks_with_data(api_client, sample_task):
    """GET /api/tasks/ should return list with existing tasks"""
    response = api_client.get('/api/tasks/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    assert any(task["id"] == sample_task["id"] for task in response.data)
    assert response.data[0]["title"] == "Buy groceries"


# ────────────────────────────────────────────────
# POST /api/tasks/  → Create task
# ────────────────────────────────────────────────

@pytest.mark.parametrize("payload, expected_status, expected_error_field", [
    ({"title": "New task"}, status.HTTP_201_CREATED, None),
    ({"title": "  "}, status.HTTP_400_BAD_REQUEST, "title"),
    ({}, status.HTTP_400_BAD_REQUEST, "title"),
    ({"title": "Valid", "status": "invalid"}, status.HTTP_201_CREATED, None),  # status not validated yet
])
def test_create_task_various_inputs(api_client, payload, expected_status, expected_error_field):
    response = api_client.post('/api/tasks/', payload, format='json')
    assert response.status_code == expected_status

    if expected_status == status.HTTP_201_CREATED:
        assert "id" in response.data
        assert response.data["title"] == payload["title"].strip()
        # cleanup
        delete_task(response.data["id"])
    else:
        assert expected_error_field in response.data


def test_create_task_full_payload(api_client):
    payload = {
        "title": "Doctor appointment",
        "description": "Checkup at 3 PM",
        "due_date": "2026-03-20",
        "status": "pending"
    }
    response = api_client.post('/api/tasks/', payload, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["description"] == payload["description"]
    assert response.data["due_date"] == date.fromisoformat(payload["due_date"])
    assert response.data["status"] == payload["status"]

    # Verify it was really saved
    saved = get_task_by_id(response.data["id"])
    assert saved is not None
    assert saved["title"] == payload["title"]


# ────────────────────────────────────────────────
# GET /api/tasks/<pk>/  → Retrieve single task
# ────────────────────────────────────────────────

def test_get_single_task_exists(api_client, sample_task):
    response = api_client.get(f'/api/tasks/{sample_task["id"]}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == sample_task["id"]
    assert response.data["title"] == "Buy groceries"


def test_get_single_task_not_found(api_client):
    response = api_client.get('/api/tasks/999999/')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Task not found" in str(response.data)


# ────────────────────────────────────────────────
# PUT /api/tasks/<pk>/  → Update task
# ────────────────────────────────────────────────

def test_update_task_full(api_client, sample_task):
    payload = {
        "title": "Buy groceries - UPDATED",
        "description": "Now also cheese",
        "due_date": "2026-03-16",
        "status": "completed"
    }
    response = api_client.put(f'/api/tasks/{sample_task["id"]}/', payload, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data["title"] == payload["title"]
    assert response.data["status"] == "completed"

    # Verify persistence
    updated = get_task_by_id(sample_task["id"])
    assert updated["status"] == "completed"


def test_update_task_partial(api_client, sample_task):
    """Partial update – only send title"""
    response = api_client.put(
        f'/api/tasks/{sample_task["id"]}/',
        {"title": "Changed title only"},
        format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["title"] == "Changed title only"
    # other fields should remain unchanged
    assert response.data["status"] == "pending"


def test_update_task_not_found(api_client):
    response = api_client.put('/api/tasks/999999/', {"title": "Ghost"}, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_task_missing_title(api_client, sample_task):
    response = api_client.put(f'/api/tasks/{sample_task["id"]}/', {}, format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "title" in response.data


# ────────────────────────────────────────────────
# DELETE /api/tasks/<pk>/  → Delete task
# ────────────────────────────────────────────────

def test_delete_task_exists(api_client, sample_task):
    response = api_client.delete(f'/api/tasks/{sample_task["id"]}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's gone
    assert get_task_by_id(sample_task["id"]) is None


def test_delete_task_not_found(api_client):
    response = api_client.delete('/api/tasks/888888/')
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ────────────────────────────────────────────────
# Bonus: Multiple tasks + ordering
# ────────────────────────────────────────────────

def test_create_multiple_tasks_check_order(api_client):
    tasks_to_create = [
        {"title": "Task C", "status": "pending"},
        {"title": "Task A", "status": "pending"},
        {"title": "Task B", "status": "pending"},
    ]

    ids = []
    for t in tasks_to_create:
        resp = api_client.post('/api/tasks/', t, format='json')
        assert resp.status_code == 201
        ids.append(resp.data["id"])

    list_resp = api_client.get('/api/tasks/')
    titles = [item["title"] for item in list_resp.data]

    # Should be ordered by created_at DESC → newest first
    # So Task B, Task A, Task C
    assert titles[:3] == ["Task B", "Task A", "Task C"]

    # cleanup
    for tid in ids:
        delete_task(tid)