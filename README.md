<<<<<<< HEAD
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
=======
# My todos

Backend service for a simple TODO list application, implemented with **Python** and **FastAPI**.

This project is designed to be a reusable backend for future applications where a TODO list service is required. You can plug it into different frontends (web, mobile, desktop) or use it as a building block in larger systems.

## Features

- Create, read, update and delete TODO items
- Simple REST API built with FastAPI
- Async request handling
- In‑memory storage (for now) – ready to be replaced with a real database later
- Automatic interactive API docs via Swagger UI and ReDoc

## Tech stack

- Python 3.11+
- FastAPI
- Uvicorn (ASGI server)

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/pelykh/my-todos.git
cd my-todos
```

### 2. Create and activate a virtual environment (optional but recommended) ￼￼
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies ￼
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
uvicorn main:app --reload
```
By default the server starts at: http://127.0.0.1:8000
>>>>>>> 6615b2562583030c3b22ff0b3c6f83dd868d34c9
