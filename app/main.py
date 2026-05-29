"""
FastAPI service — the data plane.
Agents never call this directly — they go through the MCP server.
This service owns the database and exposes clean REST endpoints.
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os

from app.database import get_db, create_tables, Transaction, Report

app = FastAPI(
    title="Transaction Triage API",
    description="Data plane for the transaction triage system",
    version="1.0.0"
)


# ── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
def on_startup():
    """Create tables on startup if they don't exist."""
    create_tables()


# ── Pydantic models (request/response shapes) ──────────────────────────────

class NoteItem(BaseModel):
    agent: str
    ts: str
    text: str


class TransactionResponse(BaseModel):
    id: str
    created_at: str
    account_from: str
    account_to: str
    amount: str
    currency: str
    counterparty: str
    memo: Optional[str]
    status: str
    notes: list

    class Config:
        from_attributes = True


class UpdateStatusRequest(BaseModel):
    status: str
    reasoning: str
    agent: str = "unknown"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"clean", "suspicious", "blocked", "needs-human-review", "pending"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Reasoning note is required and cannot be empty")
        return v


class ReportCreateRequest(BaseModel):
    content: str
    report_type: str = "morning_report"


# ── Helper ─────────────────────────────────────────────────────────────────

def tx_to_dict(tx: Transaction) -> dict:
    """Convert a Transaction ORM object to a clean dictionary."""
    return {
        "id": str(tx.id),
        "created_at": tx.created_at.isoformat() if tx.created_at else None,
        "account_from": tx.account_from,
        "account_to": tx.account_to,
        "amount": str(tx.amount),
        "currency": tx.currency,
        "counterparty": tx.counterparty,
        "memo": tx.memo,
        "status": tx.status,
        "notes": tx.notes or [],
    }


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "running", "service": "triage-api"}


@app.get("/transactions")
def list_transactions(
    status: Optional[str] = Query(None, description="Filter by status"),
    since: Optional[str] = Query(None, description="ISO timestamp — only return transactions after this time"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """
    List transactions with optional filters.
    Used by MCP list_transactions tool.
    """
    query = db.query(Transaction)

    if status:
        query = query.filter(Transaction.status == status)

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(Transaction.created_at >= since_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {since}")

    query = query.order_by(Transaction.created_at.desc()).limit(limit)
    transactions = query.all()

    return {"transactions": [tx_to_dict(tx) for tx in transactions], "count": len(transactions)}


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """
    Fetch a single transaction by ID.
    Used by MCP get_transaction tool.
    """
    try:
        tx_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    tx = db.query(Transaction).filter(Transaction.id == tx_uuid).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    return tx_to_dict(tx)


@app.patch("/transactions/{transaction_id}/status")
def update_transaction_status(
    transaction_id: str,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Update transaction status with a required reasoning note.
    Used by MCP set_transaction_status tool.
    """
    try:
        tx_uuid = uuid.UUID(transaction_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    tx = db.query(Transaction).filter(Transaction.id == tx_uuid).first()
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")

    # Add note to the notes array
    current_notes = list(tx.notes or [])
    current_notes.append({
        "agent": request.agent,
        "ts": datetime.now(timezone.utc).isoformat(),
        "text": request.reasoning
    })

    tx.status = request.status
    tx.notes = current_notes
    db.commit()
    db.refresh(tx)

    return tx_to_dict(tx)


@app.get("/metrics")
def get_metrics(
    since: Optional[str] = Query(None, description="ISO timestamp window start"),
    top_n: int = Query(5, description="Top N counterparties to return"),
    db: Session = Depends(get_db)
):
    """
    Aggregate risk metrics over a time window.
    Used by MCP get_risk_metrics tool.
    """
    query = db.query(Transaction)

    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(Transaction.created_at >= since_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {since}")

    transactions = query.all()

    # Count and total amount by status
    status_counts = {}
    status_amounts = {}
    counterparty_suspicious = {}

    for tx in transactions:
        status = tx.status
        amount = float(tx.amount or 0)

        status_counts[status] = status_counts.get(status, 0) + 1
        status_amounts[status] = status_amounts.get(status, 0.0) + amount

        if status == "suspicious":
            cp = tx.counterparty or "unknown"
            counterparty_suspicious[cp] = counterparty_suspicious.get(cp, 0) + 1

    # Top N counterparties by suspicious count
    top_counterparties = sorted(
        counterparty_suspicious.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    return {
        "count_by_status": status_counts,
        "total_amount_by_status": status_amounts,
        "top_suspicious_counterparties": [
            {"counterparty": cp, "count": count}
            for cp, count in top_counterparties
        ],
        "total_transactions": len(transactions)
    }


@app.post("/reports")
def create_report(request: ReportCreateRequest, db: Session = Depends(get_db)):
    """
    Save a report to the database.
    Also saves to reports/ directory as a markdown file.
    Used by MCP write_report tool.
    """
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Report content cannot be empty")

    report = Report(
        content=request.content,
        report_type=request.report_type
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Also save as a file
    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/morning-report-{str(report.id)[:8]}.md"
    with open(report_path, "w") as f:
        f.write(request.content)

    # Also save as the canonical morning-report.md that make verify checks
    with open("reports/morning-report.md", "w") as f:
        f.write(request.content)

    return {
        "id": str(report.id),
        "path": report_path,
        "created_at": report.created_at.isoformat()
    }


@app.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    """List all saved reports."""
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return {
        "reports": [
            {
                "id": str(r.id),
                "created_at": r.created_at.isoformat(),
                "report_type": r.report_type,
                "preview": r.content[:200] + "..." if len(r.content) > 200 else r.content
            }
            for r in reports
        ]
    }