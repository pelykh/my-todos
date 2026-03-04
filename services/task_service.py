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
        current = {k: v for k, v in vars(task).items() if not k.startswith("_")}
        return self._repo.upsert({**current, **patch, "server_version": version})

    def delete(self, task: Task) -> Task:
        return self.update(task, {"status": "deleted"})
