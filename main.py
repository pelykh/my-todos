from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from database import Base, engine
from routers import auth, tasks, sync


def _run_migrations():
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return
    cols = [c["name"] for c in inspector.get_columns("tasks")]
    with engine.connect() as conn:
        if "tags" not in cols:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN tags VARCHAR NOT NULL DEFAULT ''"))
            conn.commit()


Base.metadata.create_all(bind=engine)
_run_migrations()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(sync.router)


@app.get("/")
def read_root():
    return {"message": "Hello World"}
