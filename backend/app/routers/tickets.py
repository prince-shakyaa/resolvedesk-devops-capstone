from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Ticket, TicketComment
from ..schemas import (
    CommentCreate,
    CommentOut,
    Priority,
    StatsOut,
    Status,
    TicketCreate,
    TicketOut,
    TicketUpdate,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _comment_count_subquery():
    return (
        select(TicketComment.ticket_id, func.count(TicketComment.id).label("comment_count"))
        .group_by(TicketComment.ticket_id)
        .subquery()
    )


def _to_out(ticket: Ticket, comment_count: int | None) -> TicketOut:
    out = TicketOut.model_validate(ticket)
    out.comment_count = comment_count or 0
    return out


def _get_or_404(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    status_filter: Status | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    q: str | None = Query(default=None, description="Free-text search on subject"),
    limit: int = Query(default=100, ge=1, le=500),
):
    counts = _comment_count_subquery()
    stmt = (
        select(Ticket, counts.c.comment_count)
        .outerjoin(counts, counts.c.ticket_id == Ticket.id)
        .order_by(Ticket.id.desc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if q:
        stmt = stmt.where(Ticket.subject.ilike(f"%{q}%"))
    return [_to_out(ticket, count) for ticket, count in db.execute(stmt).all()]


@router.get("/stats", response_model=StatsOut)
def ticket_stats(db: Session = Depends(get_db)):
    status_rows = db.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)).all()
    by_status = {row_status: count for row_status, count in status_rows}

    category_rows = db.execute(select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)).all()

    urgent_open = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.priority == "URGENT", Ticket.status.in_(["OPEN", "IN_PROGRESS"])
        )
    )
    unassigned = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.assignee.is_(None), Ticket.status.in_(["OPEN", "IN_PROGRESS"])
        )
    )

    return StatsOut(
        total=sum(by_status.values()),
        open=by_status.get("OPEN", 0),
        in_progress=by_status.get("IN_PROGRESS", 0),
        resolved=by_status.get("RESOLVED", 0),
        closed=by_status.get("CLOSED", 0),
        urgent_open=urgent_open or 0,
        unassigned=unassigned or 0,
        by_category={category: count for category, count in category_rows},
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    return _to_out(ticket, len(ticket.comments))


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return _to_out(ticket, 0)


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="No fields supplied for update")

    for key, value in changes.items():
        setattr(ticket, key, value)

    new_status = changes.get("status")
    if new_status in ("RESOLVED", "CLOSED") and ticket.resolved_at is None:
        ticket.resolved_at = datetime.now(UTC)
    elif new_status in ("OPEN", "IN_PROGRESS"):
        ticket.resolved_at = None

    db.commit()
    db.refresh(ticket)
    return _to_out(ticket, len(ticket.comments))


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    db.delete(ticket)
    db.commit()
    return None


@router.get("/{ticket_id}/comments", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    return ticket.comments


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(ticket_id: int, payload: CommentCreate, db: Session = Depends(get_db)):
    ticket = _get_or_404(db, ticket_id)
    comment = TicketComment(ticket_id=ticket.id, **payload.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
