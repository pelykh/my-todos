from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Task
from repositories.base import BaseRepository


class TaskRepository(BaseRepository["Task"]):
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
