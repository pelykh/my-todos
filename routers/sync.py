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
