# tests/conftest.py
import pytest
from rest_framework.test import APIClient
from task.utils import init_database
from task.views import  create_task

# @pytest.fixture(autouse=True)
@pytest.mark.django_db
def enable_db():
    pass


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Run once per test session — create table only once"""
    with django_db_blocker.unblock():
        init_database()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):   # ← uses the built-in 'db' fixture
    pass  # this is enough — all tests below will have DB access


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def sample_task(db):
    task_id = create_task(
        title="Buy groceries",
        description="Milk, bread, eggs",
        due_date="2026-03-15",
        status="pending"
    )
    return {"id": task_id, "title": "Buy groceries"}
# @pytest.fixture
# def sample_task(db):   # ← request 'db' fixture → enables DB
#     task_id = create_task(
#         title="Sample task for testing",
#         description="This is auto-created",
#         due_date="2026-03-20",
#         status="pending"
#     )

#     yield {"id": task_id, "title": "Sample task for testing"}
    # optional: cleanup
    # from task.utils import delete_task
    # delete_task(task_id)