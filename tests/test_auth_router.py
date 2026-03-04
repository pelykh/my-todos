def test_register_success(client):
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    resp = client.post("/auth/register", json={"email": "a@b.com", "password": "other"})
    assert resp.status_code == 409


def test_login_success(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "a@b.com", "password": "secret123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "a@b.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={"email": "nobody@b.com", "password": "x"})
    assert resp.status_code == 401
