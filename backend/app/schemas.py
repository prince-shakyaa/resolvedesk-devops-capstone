from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
Priority = Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
Category = Literal["HARDWARE", "SOFTWARE", "NETWORK", "ACCESS", "OTHER"]


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = ""
    category: Category = "SOFTWARE"
    priority: Priority = "MEDIUM"
    requester: str = Field(min_length=1, max_length=120)
    assignee: str | None = Field(default=None, max_length=120)


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    category: Category | None = None
    priority: Priority | None = None
    status: Status | None = None
    requester: str | None = Field(default=None, min_length=1, max_length=120)
    assignee: str | None = Field(default=None, max_length=120)


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    description: str
    category: Category
    priority: Priority
    status: Status
    requester: str
    assignee: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    comment_count: int = 0


class CommentCreate(BaseModel):
    author: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author: str
    body: str
    created_at: datetime


class StatsOut(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int
    urgent_open: int
    unassigned: int
    by_category: dict[str, int]
