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
