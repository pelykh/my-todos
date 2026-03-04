import uuid


def _task(id=None):
    return {
        "id": id or str(uuid.uuid4()),
        "title": "Buy milk",
        "status": "inbox",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }


def test_create_and_list_task(auth_client):
    auth_client.post("/tasks", json=_task(id="t1"))
    resp = auth_client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == "t1"


def test_list_excludes_deleted(auth_client):
    auth_client.post("/tasks", json=_task(id="t1"))
    auth_client.delete("/tasks/t1")
    resp = auth_client.get("/tasks")
    assert resp.json() == []


def test_get_task(auth_client):
    auth_client.post("/tasks", json=_task(id="t1"))
    resp = auth_client.get("/tasks/t1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "t1"


def test_get_task_not_found(auth_client):
    resp = auth_client.get("/tasks/nonexistent")
    assert resp.status_code == 404


def test_patch_task(auth_client):
    auth_client.post("/tasks", json=_task(id="t1"))
    resp = auth_client.patch("/tasks/t1", json={"title": "Updated", "updated_at": "2026-01-02T00:00:00Z"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_delete_task(auth_client):
    auth_client.post("/tasks", json=_task(id="t1"))
    resp = auth_client.delete("/tasks/t1")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"


def test_tasks_are_user_scoped(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass1word"})
    r1 = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1word"})
    token1 = r1.json()["access_token"]

    client.post("/auth/register", json={"email": "b@b.com", "password": "pass2word"})
    r2 = client.post("/auth/login", json={"email": "b@b.com", "password": "pass2word"})
    token2 = r2.json()["access_token"]

    client.post("/tasks", json=_task(id="t1"), headers={"Authorization": f"Bearer {token1}"})
    resp = client.get("/tasks", headers={"Authorization": f"Bearer {token2}"})
    assert resp.json() == []
