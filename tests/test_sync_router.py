import uuid


def _task(id=None):
    return {
        "id": id or str(uuid.uuid4()),
        "title": "Task",
        "status": "inbox",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def test_sync_push_returns_version(auth_client):
    resp = auth_client.post("/sync", json={"changes": [_task(id="t1"), _task(id="t2")]})
    assert resp.status_code == 200
    assert resp.json()["server_version"] == 2


def test_sync_pull_since(auth_client):
    auth_client.post("/sync", json={"changes": [_task(id="t1")]})
    auth_client.post("/sync", json={"changes": [_task(id="t2")]})
    resp = auth_client.get("/sync?since=1")
    assert resp.status_code == 200
    tasks = resp.json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t2"


def test_sync_pull_since_zero_returns_all(auth_client):
    auth_client.post("/sync", json={"changes": [_task(id="t1"), _task(id="t2")]})
    resp = auth_client.get("/sync?since=0")
    assert len(resp.json()["tasks"]) == 2


def test_sync_requires_auth(client):
    resp = client.post("/sync", json={"changes": []})
    assert resp.status_code in (401, 403)
