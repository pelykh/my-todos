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
        if not changes:
            return self._repo.max_version(user_id)
        start_version = self._repo.max_version(user_id)
        for i, change in enumerate(changes, start=1):
            if isinstance(change.get("tags"), list):
                change = {**change, "tags": " ".join(sorted(change["tags"]))}
            self._repo.upsert({**change, "user_id": user_id, "server_version": start_version + i})
        return start_version + len(changes)

    def pull(self, user_id: str, since: int) -> list:
        return self._repo.get_since(user_id, since)
