from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from services.task_service import TaskService


def _make_task_data(id="t1", user_id="u1"):
    return {
        "id": id,
        "title": "Buy milk",
        "status": "inbox",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def test_create_task_assigns_server_version(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    svc = TaskService(TaskRepository(db))
    task = svc.create(user_id=user.id, data=_make_task_data(user_id=user.id))
    assert task.server_version == 1


def test_update_task_bumps_server_version(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    repo = TaskRepository(db)
    svc = TaskService(repo)
    t1 = svc.create(user_id=user.id, data=_make_task_data(id="t1", user_id=user.id))
    svc.create(user_id=user.id, data=_make_task_data(id="t2", user_id=user.id))
    updated = svc.update(task=t1, patch={"title": "Updated", "updated_at": "2026-01-02T00:00:00Z"})
    assert updated.server_version == 3


def test_soft_delete_sets_status(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    repo = TaskRepository(db)
    svc = TaskService(repo)
    task = svc.create(user_id=user.id, data=_make_task_data(user_id=user.id))
    deleted = svc.delete(task=task)
    assert deleted.status == "deleted"
