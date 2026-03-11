# Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI backend with SQLite (swappable to Postgres), email+password JWT auth, task CRUD, and a delta sync protocol with SSE push notifications.

**Architecture:** Layered Repository pattern — routers call services, services call repositories, repositories are the only layer that touches SQLAlchemy. Swapping SQLite → Postgres requires changing one URL in `config.py`.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, SQLite, PyJWT, passlib[bcrypt], sse-starlette, pytest, httpx

---

### Task 1: Install dependencies and create config + database setup

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `database.py`

**Step 1: Install dependencies**

```bash
source venv/bin/activate
pip install "passlib[bcrypt]" PyJWT sse-starlette pytest httpx python-multipart
pip freeze > requirements.txt
```

**Step 2: Create `config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./todos.db"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_days: int = 30

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
```

Note: `pydantic-settings` ships with FastAPI's extras. If the import fails, run `pip install pydantic-settings`.

**Step 3: Create `database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Verify no import errors**

```bash
source venv/bin/activate && python -c "import database; print('OK')"
```

Expected: `OK`

**Step 5: Commit**

```bash
git add requirements.txt config.py database.py
git commit -m "feat: add project config and database setup"
```

---

### Task 2: SQLAlchemy models

**Files:**
- Create: `models.py`

**Step 1: Write `models.py`**

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="inbox")
    context: Mapped[str | None] = mapped_column(String, nullable=True)
    area: Mapped[str | None] = mapped_column(String, nullable=True)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True)
    is_project: Mapped[bool] = mapped_column(Boolean, default=False)
    scheduled_date: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_since: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    server_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    user: Mapped["User"] = relationship("User", back_populates="tasks")
```

**Step 2: Verify models load and create tables**

```bash
source venv/bin/activate && python -c "
from database import engine, Base
import models
Base.metadata.create_all(bind=engine)
print('Tables created OK')
"
```

Expected: `Tables created OK`

**Step 3: Commit**

```bash
git add models.py
git commit -m "feat: add SQLAlchemy models for User and Task"
```

---

### Task 3: Pydantic schemas

**Files:**
- Create: `schemas.py`

**Step 1: Write `schemas.py`**

```python
from __future__ import annotations

from pydantic import BaseModel, EmailStr


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Task ---

class TaskSchema(BaseModel):
    id: str
    title: str
    notes: str | None = None
    status: str = "inbox"
    context: str | None = None
    area: str | None = None
    project_id: str | None = None
    is_project: bool = False
    scheduled_date: str | None = None
    due_date: str | None = None
    estimated_minutes: int | None = None
    waiting_since: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None

    model_config = {"from_attributes": True}


class TaskPatchRequest(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    context: str | None = None
    area: str | None = None
    project_id: str | None = None
    is_project: bool | None = None
    scheduled_date: str | None = None
    due_date: str | None = None
    estimated_minutes: int | None = None
    waiting_since: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


# --- Sync ---

class SyncPushRequest(BaseModel):
    changes: list[TaskSchema]


class SyncPushResponse(BaseModel):
    server_version: int


class SyncPullResponse(BaseModel):
    tasks: list[TaskSchema]
```

Note: `EmailStr` requires `pip install "pydantic[email]"` — run that if the import fails.

**Step 2: Verify schemas load**

```bash
source venv/bin/activate && python -c "import schemas; print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add schemas.py
git commit -m "feat: add Pydantic schemas"
```

---

### Task 4: Test infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create `tests/__init__.py`**

```python
```

(empty file)

**Step 2: Create `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(setup_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(setup_db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """Returns a TestClient with a registered+logged-in user and auth headers."""
    client.post("/auth/register", json={"email": "test@example.com", "password": "secret123"})
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "secret123"})
    token = resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
```

**Step 3: Verify pytest can collect (no tests yet, just check it runs)**

```bash
source venv/bin/activate && python -m pytest tests/ -v 2>&1 | head -20
```

Expected: no collection errors (may show "no tests ran")

**Step 4: Commit**

```bash
git add tests/
git commit -m "feat: add test infrastructure and conftest"
```

---

### Task 5: Repository layer

**Files:**
- Create: `repositories/__init__.py`
- Create: `repositories/base.py`
- Create: `repositories/user_repository.py`
- Create: `repositories/task_repository.py`
- Create: `tests/test_repositories.py`

**Step 1: Write failing tests**

Create `tests/test_repositories.py`:

```python
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
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_repositories.py -v
```

Expected: ImportError or ModuleNotFoundError

**Step 3: Create `repositories/__init__.py`**

```python
```

(empty)

**Step 4: Create `repositories/base.py`**

```python
from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
```

**Step 5: Create `repositories/user_repository.py`**

```python
from sqlalchemy.orm import Session

from models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
```

**Step 6: Create `repositories/task_repository.py`**

```python
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Task
from repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    def upsert(self, data: dict) -> Task:
        task = self.db.query(Task).filter(Task.id == data["id"]).first()
        if task is None:
            task = Task(**data)
            self.db.add(task)
        else:
            for key, value in data.items():
                setattr(task, key, value)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: str, user_id: str) -> Task | None:
        return (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.user_id == user_id)
            .first()
        )

    def list_for_user(self, user_id: str) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id, Task.status != "deleted")
            .all()
        )

    def get_since(self, user_id: str, since: int) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.user_id == user_id, Task.server_version > since)
            .all()
        )

    def max_version(self, user_id: str) -> int:
        result = self.db.query(func.max(Task.server_version)).filter(Task.user_id == user_id).scalar()
        return result or 0
```

**Step 7: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_repositories.py -v
```

Expected: all PASS

**Step 8: Commit**

```bash
git add repositories/ tests/test_repositories.py
git commit -m "feat: add repository layer with tests"
```

---

### Task 6: Auth service

**Files:**
- Create: `services/__init__.py`
- Create: `services/auth_service.py`
- Create: `tests/test_auth_service.py`

**Step 1: Write failing tests**

Create `tests/test_auth_service.py`:

```python
import pytest
import jwt

from services.auth_service import AuthService


def test_hash_and_verify_password():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    hashed = svc.hash_password("mypassword")
    assert hashed != "mypassword"
    assert svc.verify_password("mypassword", hashed)
    assert not svc.verify_password("wrong", hashed)


def test_create_and_decode_token():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    token = svc.create_token(user_id="user-123")
    user_id = svc.decode_token(token)
    assert user_id == "user-123"


def test_decode_invalid_token_raises():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    with pytest.raises(jwt.InvalidTokenError):
        svc.decode_token("not.a.token")
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_auth_service.py -v
```

Expected: ImportError

**Step 3: Create `services/__init__.py`**

```python
```

(empty)

**Step 4: Create `services/auth_service.py`**

```python
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext


class AuthService:
    def __init__(self, jwt_secret: str, jwt_expire_days: int) -> None:
        self._secret = jwt_secret
        self._expire_days = jwt_expire_days
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)

    def create_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=self._expire_days),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode_token(self, token: str) -> str:
        payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        return payload["sub"]
```

**Step 5: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_auth_service.py -v
```

Expected: all PASS

**Step 6: Commit**

```bash
git add services/ tests/test_auth_service.py
git commit -m "feat: add auth service (JWT + bcrypt) with tests"
```

---

### Task 7: Task service

**Files:**
- Create: `services/task_service.py`
- Create: `tests/test_task_service.py`

**Step 1: Write failing tests**

Create `tests/test_task_service.py`:

```python
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
    t2 = svc.create(user_id=user.id, data=_make_task_data(id="t2", user_id=user.id))
    updated = svc.update(task=t1, patch={"title": "Updated", "updated_at": "2026-01-02T00:00:00Z"})
    assert updated.server_version == 3


def test_soft_delete_sets_status(db):
    user = UserRepository(db).create(email="a@b.com", password_hash="h")
    repo = TaskRepository(db)
    svc = TaskService(repo)
    task = svc.create(user_id=user.id, data=_make_task_data(user_id=user.id))
    deleted = svc.delete(task=task)
    assert deleted.status == "deleted"
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_task_service.py -v
```

Expected: ImportError

**Step 3: Create `services/task_service.py`**

```python
from models import Task
from repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    def _next_version(self, user_id: str) -> int:
        return self._repo.max_version(user_id) + 1

    def create(self, user_id: str, data: dict) -> Task:
        version = self._next_version(user_id)
        return self._repo.upsert({**data, "user_id": user_id, "server_version": version})

    def update(self, task: Task, patch: dict) -> Task:
        version = self._next_version(task.user_id)
        return self._repo.upsert({
            "id": task.id,
            "user_id": task.user_id,
            **{k: v for k, v in vars(task).items() if not k.startswith("_")},
            **patch,
            "server_version": version,
        })

    def delete(self, task: Task) -> Task:
        return self.update(task, {"status": "deleted"})
```

**Step 4: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_task_service.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add services/task_service.py tests/test_task_service.py
git commit -m "feat: add task service with server_version logic"
```

---

### Task 8: Sync service + SSE broadcaster

**Files:**
- Create: `services/sync_service.py`
- Create: `tests/test_sync_service.py`

**Step 1: Write failing tests**

Create `tests/test_sync_service.py`:

```python
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


@pytest.mark.asyncio
async def test_sse_broadcaster_delivers_message():
    broadcaster = SSEBroadcaster()
    q = broadcaster.subscribe("user-1")
    await broadcaster.broadcast("user-1")
    msg = await asyncio.wait_for(q.get(), timeout=1)
    assert msg == "change"
    broadcaster.unsubscribe("user-1", q)
```

**Step 2: Install pytest-asyncio**

```bash
source venv/bin/activate && pip install pytest-asyncio && pip freeze > requirements.txt
```

Add `pytest.ini` (or `pyproject.toml` section) to configure asyncio mode:

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
```

**Step 3: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_sync_service.py -v
```

Expected: ImportError

**Step 4: Create `services/sync_service.py`**

```python
import asyncio
from collections import defaultdict

from repositories.task_repository import TaskRepository


class SSEBroadcaster:
    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def subscribe(self, user_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[user_id].add(q)
        return q

    def unsubscribe(self, user_id: str, q: asyncio.Queue) -> None:
        self._queues[user_id].discard(q)

    async def broadcast(self, user_id: str) -> None:
        for q in list(self._queues[user_id]):
            await q.put("change")


# Module-level singleton shared across requests
broadcaster = SSEBroadcaster()


def get_broadcaster() -> SSEBroadcaster:
    return broadcaster


class SyncService:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    def push(self, user_id: str, changes: list[dict]) -> int:
        """Store all changes, assigning monotonic server_version. Returns final version."""
        for change in changes:
            current_max = self._repo.max_version(user_id)
            self._repo.upsert({**change, "user_id": user_id, "server_version": current_max + 1})
        return self._repo.max_version(user_id)

    def pull(self, user_id: str, since: int) -> list:
        return self._repo.get_since(user_id, since)
```

**Step 5: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_sync_service.py -v
```

Expected: all PASS

**Step 6: Commit**

```bash
git add services/sync_service.py tests/test_sync_service.py pytest.ini requirements.txt
git commit -m "feat: add sync service and SSE broadcaster"
```

---

### Task 9: Auth router

**Files:**
- Create: `routers/__init__.py`
- Create: `routers/auth.py`
- Create: `routers/deps.py`
- Create: `tests/test_auth_router.py`

**Step 1: Write failing tests**

Create `tests/test_auth_router.py`:

```python
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
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_auth_router.py -v
```

Expected: ImportError or 404

**Step 3: Create `routers/__init__.py`**

```python
```

(empty)

**Step 4: Create `routers/deps.py`** (shared dependency: get current user)

```python
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import Settings, get_settings
from database import get_db
from models import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

security = HTTPBearer()


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(jwt_secret=settings.jwt_secret, jwt_expire_days=settings.jwt_expire_days)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
) -> User:
    try:
        user_id = auth_svc.decode_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

**Step 5: Create `routers/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from repositories.user_repository import UserRepository
from routers.deps import get_auth_service
from schemas import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
):
    repo = UserRepository(db)
    if repo.get_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = repo.create(email=body.email, password_hash=auth_svc.hash_password(body.password))
    return TokenResponse(access_token=auth_svc.create_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if user is None or not auth_svc.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=auth_svc.create_token(user.id))
```

**Step 6: Update `main.py` to mount the auth router**

```python
from fastapi import FastAPI
from database import Base, engine
from routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

**Step 7: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_auth_router.py -v
```

Expected: all PASS

**Step 8: Commit**

```bash
git add routers/ tests/test_auth_router.py main.py
git commit -m "feat: add auth router (register + login)"
```

---

### Task 10: Tasks router

**Files:**
- Create: `routers/tasks.py`
- Create: `tests/test_tasks_router.py`

**Step 1: Write failing tests**

Create `tests/test_tasks_router.py`:

```python
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
    """Two users cannot see each other's tasks."""
    client.post("/auth/register", json={"email": "a@b.com", "password": "pass1"})
    r1 = client.post("/auth/login", json={"email": "a@b.com", "password": "pass1"})
    token1 = r1.json()["access_token"]

    client.post("/auth/register", json={"email": "b@b.com", "password": "pass2"})
    r2 = client.post("/auth/login", json={"email": "b@b.com", "password": "pass2"})
    token2 = r2.json()["access_token"]

    client.post("/tasks", json=_task(id="t1"), headers={"Authorization": f"Bearer {token1}"})
    resp = client.get("/tasks", headers={"Authorization": f"Bearer {token2}"})
    assert resp.json() == []
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_tasks_router.py -v
```

Expected: 404 (router not mounted yet)

**Step 3: Create `routers/tasks.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from repositories.task_repository import TaskRepository
from routers.deps import get_current_user
from schemas import TaskPatchRequest, TaskSchema
from services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task_or_404(task_id: str, user: User, db: Session):
    task = TaskRepository(db).get_by_id(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("", response_model=list[TaskSchema])
def list_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TaskRepository(db).list_for_user(current_user.id)


@router.get("/{task_id}", response_model=TaskSchema)
def get_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_task_or_404(task_id, current_user, db)


@router.post("", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TaskService(TaskRepository(db))
    return svc.create(user_id=current_user.id, data=body.model_dump())


@router.patch("/{task_id}", response_model=TaskSchema)
def update_task(
    task_id: str,
    body: TaskPatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user, db)
    svc = TaskService(TaskRepository(db))
    return svc.update(task, body.model_dump(exclude_none=True))


@router.delete("/{task_id}", response_model=TaskSchema)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user, db)
    return TaskService(TaskRepository(db)).delete(task)
```

**Step 4: Mount router in `main.py`**

```python
from fastapi import FastAPI
from database import Base, engine
from routers import auth, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

**Step 5: Fix `POST /tasks` status code in conftest** — `TestClient` follows redirects by default; the 201 status is fine. No change needed.

**Step 6: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_tasks_router.py -v
```

Expected: all PASS

**Step 7: Commit**

```bash
git add routers/tasks.py tests/test_tasks_router.py main.py
git commit -m "feat: add tasks CRUD router with user scoping"
```

---

### Task 11: Sync router + SSE

**Files:**
- Create: `routers/sync.py`
- Create: `tests/test_sync_router.py`

**Step 1: Write failing tests**

Create `tests/test_sync_router.py`:

```python
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
    assert resp.status_code == 403
```

**Step 2: Run tests — expect failures**

```bash
source venv/bin/activate && python -m pytest tests/test_sync_router.py -v
```

Expected: 404

**Step 3: Create `routers/sync.py`**

```python
import asyncio

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User
from repositories.task_repository import TaskRepository
from routers.deps import get_current_user
from schemas import SyncPullResponse, SyncPushRequest, SyncPushResponse
from services.sync_service import SSEBroadcaster, SyncService, get_broadcaster

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncPushResponse)
async def sync_push(
    body: SyncPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    broadcaster: SSEBroadcaster = Depends(get_broadcaster),
):
    svc = SyncService(TaskRepository(db))
    version = svc.push(user_id=current_user.id, changes=[c.model_dump() for c in body.changes])
    await broadcaster.broadcast(current_user.id)
    return SyncPushResponse(server_version=version)


@router.get("/sync", response_model=SyncPullResponse)
def sync_pull(
    since: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = SyncService(TaskRepository(db))
    tasks = svc.pull(user_id=current_user.id, since=since)
    return SyncPullResponse(tasks=tasks)


@router.get("/events")
async def sse_events(
    request: Request,
    current_user: User = Depends(get_current_user),
    broadcaster: SSEBroadcaster = Depends(get_broadcaster),
):
    async def event_generator():
        q = broadcaster.subscribe(current_user.id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    await asyncio.wait_for(q.get(), timeout=30)
                    yield "data: {\"type\":\"change\"}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\":\"ping\"}\n\n"
        finally:
            broadcaster.unsubscribe(current_user.id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Step 4: Mount router in `main.py`**

```python
from fastapi import FastAPI
from database import Base, engine
from routers import auth, tasks, sync

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(sync.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
```

**Step 5: Run tests — expect pass**

```bash
source venv/bin/activate && python -m pytest tests/test_sync_router.py -v
```

Expected: all PASS

**Step 6: Run the full test suite**

```bash
source venv/bin/activate && python -m pytest tests/ -v
```

Expected: all PASS

**Step 7: Commit**

```bash
git add routers/sync.py tests/test_sync_router.py main.py
git commit -m "feat: add sync push/pull endpoints and SSE /events"
```

---

### Task 12: Smoke test the running server

**Step 1: Start the server**

```bash
source venv/bin/activate && uvicorn main:app --reload
```

**Step 2: Verify OpenAPI docs load**

Open `http://localhost:8000/docs` in a browser. You should see all endpoints listed: `/auth/register`, `/auth/login`, `/tasks`, `/sync`, `/events`.

**Step 3: Quick curl smoke test**

```bash
# Register
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"pass123"}' | python -m json.tool

# Login and capture token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"me@example.com","password":"pass123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a task
curl -s -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"abc-123","title":"Test task","status":"inbox","created_at":"2026-03-03T00:00:00Z","updated_at":"2026-03-03T00:00:00Z"}' | python -m json.tool

# List tasks
curl -s http://localhost:8000/tasks -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Push sync
curl -s -X POST http://localhost:8000/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"changes":[{"id":"xyz-456","title":"Synced task","status":"inbox","created_at":"2026-03-03T00:00:00Z","updated_at":"2026-03-03T00:00:00Z"}]}' | python -m json.tool
```

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete FastAPI backend with auth, tasks CRUD, and sync+SSE"
```
