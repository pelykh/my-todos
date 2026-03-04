import pytest
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository


def make_task(id="task-1", user_id="user-1", server_version=1):
    return {
        "id": id,
        "user_id": user_id,
        "title": "Test task",
        "status": "inbox",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "server_version": server_version,
    }


def test_user_create_and_get(db):
    repo = UserRepository(db)
    user = repo.create(email="a@b.com", password_hash="hash")
    assert user.id is not None
    assert user.email == "a@b.com"
    found = repo.get_by_email("a@b.com")
    assert found.id == user.id


def test_user_get_by_id(db):
    repo = UserRepository(db)
    user = repo.create(email="a@b.com", password_hash="hash")
    found = repo.get_by_id(user.id)
    assert found.email == "a@b.com"


def test_task_upsert_and_list(db):
    user_repo = UserRepository(db)
    user = user_repo.create(email="a@b.com", password_hash="hash")

    repo = TaskRepository(db)
    task_data = make_task(user_id=user.id)
    repo.upsert(task_data)

    tasks = repo.list_for_user(user.id)
    assert len(tasks) == 1
    assert tasks[0].title == "Test task"


def test_task_list_excludes_deleted(db):
    user_repo = UserRepository(db)
    user = user_repo.create(email="a@b.com", password_hash="hash")

    repo = TaskRepository(db)
    repo.upsert({**make_task(user_id=user.id), "status": "deleted"})

    tasks = repo.list_for_user(user.id)
    assert len(tasks) == 0


def test_task_get_since_version(db):
    user_repo = UserRepository(db)
    user = user_repo.create(email="a@b.com", password_hash="hash")

    repo = TaskRepository(db)
    repo.upsert(make_task(id="t1", user_id=user.id, server_version=1))
    repo.upsert(make_task(id="t2", user_id=user.id, server_version=2))
    repo.upsert(make_task(id="t3", user_id=user.id, server_version=5))

    tasks = repo.get_since(user.id, since=2)
    assert len(tasks) == 1
    assert tasks[0].id == "t3"


def test_task_max_version(db):
    user_repo = UserRepository(db)
    user = user_repo.create(email="a@b.com", password_hash="hash")

    repo = TaskRepository(db)
    assert repo.max_version(user.id) == 0
    repo.upsert(make_task(id="t1", user_id=user.id, server_version=3))
    assert repo.max_version(user.id) == 3
