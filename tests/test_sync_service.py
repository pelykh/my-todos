import asyncio
import pytest
from services.sync_service import SSEBroadcaster, SyncService
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository


def test_sync_push_assigns_versions(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    repo = TaskRepository(db)
    svc = SyncService(repo)

    changes = [
        {"id": "t1", "title": "A", "status": "inbox",
         "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
        {"id": "t2", "title": "B", "status": "inbox",
         "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
    ]
    version = svc.push(user_id=user.id, changes=changes)
    assert version == 2


def test_sync_pull_returns_delta(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    repo = TaskRepository(db)
    svc = SyncService(repo)

    svc.push(user_id=user.id, changes=[
        {"id": "t1", "title": "A", "status": "inbox",
         "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
    ])
    svc.push(user_id=user.id, changes=[
        {"id": "t2", "title": "B", "status": "inbox",
         "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"},
    ])

    delta = svc.pull(user_id=user.id, since=1)
    assert len(delta) == 1
    assert delta[0].id == "t2"


async def test_sse_broadcaster_delivers_message():
    broadcaster = SSEBroadcaster()
    q = broadcaster.subscribe("user-1")
    await broadcaster.broadcast("user-1")
    msg = await asyncio.wait_for(q.get(), timeout=1)
    assert msg == "change"
    broadcaster.unsubscribe("user-1", q)
