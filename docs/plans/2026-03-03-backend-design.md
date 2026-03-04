# Backend Design — my-todos FastAPI

**Date:** 2026-03-03

## Overview

FastAPI + SQLAlchemy backend for the my-todos app. Supports multi-device sync via a monotonic server version counter and SSE notifications. Auth via email + password → JWT.

---

## Architecture: Layered (Repository Pattern)

Chosen for SOLID compliance and easy DB swap (SQLite → Postgres = change one URL in `config.py`).

```
my-todos/
├── main.py                  # app factory, mounts routers
├── database.py              # engine + session factory
├── models.py                # SQLAlchemy ORM models
├── schemas.py               # Pydantic request/response schemas
├── config.py                # settings (DB URL, JWT secret, etc.)
├── repositories/
│   ├── base.py              # abstract BaseRepository[T]
│   ├── task_repository.py
│   └── user_repository.py
├── services/
│   ├── auth_service.py      # password hashing, JWT issue/verify
│   ├── task_service.py      # business logic, version bumping
│   └── sync_service.py      # push/pull logic, SSE broadcaster
├── routers/
│   ├── auth.py              # /auth/register, /auth/login
│   ├── tasks.py             # /tasks CRUD
│   └── sync.py              # /sync push/pull, /events SSE
└── requirements.txt
```

---

## Database Schema

### `users`
| column | type | notes |
|---|---|---|
| id | str (UUID) | primary key |
| email | str | unique, indexed |
| password_hash | str | bcrypt |
| created_at | datetime | server-set |

### `tasks`
| column | type | notes |
|---|---|---|
| id | str (UUID) | client-generated primary key |
| user_id | str | FK → users.id |
| title | str | |
| notes | str? | |
| status | str | plain string — `inbox`, `done`, `deleted`, etc. |
| context | str? | any string |
| area | str? | any string |
| project_id | str? | |
| is_project | bool | default false |
| scheduled_date | str? | ISO date string |
| due_date | str? | ISO date string |
| estimated_minutes | int? | |
| waiting_since | str? | ISO date string |
| created_at | str | ISO datetime, client-set |
| updated_at | str | ISO datetime, client-set |
| completed_at | str? | ISO datetime, client-set |
| server_version | int | monotonic counter, server-assigned on every write |

**Notes:**
- `context` and `area` are plain strings — no enums in DB, easy to extend on the frontend without migrations
- Soft deletes via `status = 'deleted'` — no separate `is_deleted` column
- `server_version` is per-user monotonic (`MAX(server_version) + 1`); immune to clock skew

---

## API Surface

### Auth
```
POST /auth/register   { email, password } → { access_token }
POST /auth/login      { email, password } → { access_token }
```
JWT in `Authorization: Bearer <token>` on all protected endpoints.

### Tasks (CRUD)
```
GET    /tasks          → list tasks (excludes status='deleted')
GET    /tasks/{id}     → single task
POST   /tasks          → create (client sends id + all fields)
PATCH  /tasks/{id}     → partial update
DELETE /tasks/{id}     → sets status='deleted', bumps server_version
```

### Sync
```
POST /sync   { changes: Task[] }   → { server_version: int }
GET  /sync?since={version}         → Task[]
```

### SSE
```
GET  /events   → text/event-stream
```
Fires a minimal `{ type: "change" }` event whenever any task for the authenticated user is written. Client follows up with `GET /sync?since=last_version`.

---

## Sync Protocol

1. **Client pushes** — `POST /sync` with all local changes since last sync
2. **Server stores** them, assigns monotonic `server_version` to each, fires SSE event to all connected clients for that user
3. **Client pulls** — `GET /sync?since=last_known_version` to get all changes with `server_version > since`
4. **Client applies** — last-write-wins by `server_version` (highest version wins)

**Frontend state to persist:**
- `lastSyncVersion: number` (starts at 0)
- `pendingChanges: Task[]` (offline queue)

**Multi-device flow:**
1. Phone edits task → `POST /sync` → server bumps version → SSE fires to all connected clients
2. Laptop SSE listener wakes → `GET /sync?since=last_version` → applies delta → UI updates

---

## Auth Flow

- Passwords hashed with bcrypt
- JWT tokens: `{ sub: user_id, exp: 30 days }`
- No refresh tokens initially — keep it simple
- All tokens stateless; multi-device works naturally (any device can hold a valid JWT)

---

## DB Swap (SQLite → Postgres)

Only `config.py` changes:
```python
# SQLite
DATABASE_URL = "sqlite:///./todos.db"

# Postgres
DATABASE_URL = "postgresql://user:pass@host/db"
```

No other code changes needed — SQLAlchemy abstracts the rest.
