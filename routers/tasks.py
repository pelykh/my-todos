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
