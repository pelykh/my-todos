from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Annotated


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Task ---

class TaskSchema(BaseModel):
    id: str
    title: str
    notes: str | None = None
    status: str = "inbox"
    context: str | None = None
    area: str | None = None
    project_id: str | None = None
    is_project: bool = False
    scheduled_date: str | None = None
    due_date: str | None = None
    estimated_minutes: int | None = None
    waiting_since: str | None = None
    created_at: str
    updated_at: str
    completed_at: str | None = None

    model_config = {"from_attributes": True}


class TaskPatchRequest(BaseModel):
    title: str | None = None
    notes: str | None = None
    status: str | None = None
    context: str | None = None
    area: str | None = None
    project_id: str | None = None
    is_project: bool | None = None
    scheduled_date: str | None = None
    due_date: str | None = None
    estimated_minutes: int | None = None
    waiting_since: str | None = None
    updated_at: str | None = None
    completed_at: str | None = None


# --- Sync ---

class SyncPushRequest(BaseModel):
    changes: list[TaskSchema]


class SyncPushResponse(BaseModel):
    server_version: int


class SyncPullResponse(BaseModel):
    tasks: list[TaskSchema]
