# my-todos backend

FastAPI backend for my-todos. SQLite by default, swappable to Postgres via one env var.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
JWT_SECRET=your-secret-here
# Optional:
# DATABASE_URL=sqlite:///./todos.db
# JWT_EXPIRE_DAYS=30
```

## Run

```bash
uvicorn main:app --reload
```

API docs at `http://localhost:8000/docs`.

## Swap to Postgres

```
DATABASE_URL=postgresql://user:pass@host/db
```

No other changes needed.

## API

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register `{ email, password }` → `{ access_token }` |
| POST | `/auth/login` | Login `{ email, password }` → `{ access_token }` |

All other endpoints require `Authorization: Bearer <token>`.

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List tasks (excludes deleted) |
| GET | `/tasks/{id}` | Get single task |
| POST | `/tasks` | Create task (client supplies `id`) |
| PATCH | `/tasks/{id}` | Partial update |
| DELETE | `/tasks/{id}` | Soft delete (sets `status="deleted"`) |

### Sync
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync` | Push local changes → `{ server_version }` |
| GET | `/sync?since=N` | Pull changes since version N → `{ tasks }` |
| GET | `/events` | SSE stream — fires `{"type":"change"}` when data changes |

### Sync protocol

1. On startup: `GET /sync?since=0` to pull all tasks
2. On local change: `POST /sync` with changed tasks, save returned `server_version`
3. SSE listener calls `GET /sync?since=<last_version>` on each `change` event

## Tests

```bash
JWT_SECRET=test pytest tests/ -v
```
