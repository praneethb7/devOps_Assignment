import logging
import time
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Response, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from .database import get_db
from .models import Equipment, Loan
from .schemas import EquipmentInput, EquipmentOutput, LoanInput, LoanOutput

app = FastAPI(title="CampusCrate API", version="1.0.0")
logger = logging.getLogger("uvicorn.error")
requests = Counter("campuscrate_http_requests_total", "HTTP responses", ["method", "route", "status"])
latency = Histogram("campuscrate_http_request_duration_seconds", "HTTP request duration", ["method", "route"])

def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

def active_count(db, equipment_id):
    return db.scalar(select(func.count()).select_from(Loan).where(Loan.equipment_id == equipment_id, Loan.returned_at.is_(None)))

def equipment_view(db, item):
    return EquipmentOutput(id=item.id, name=item.name, category=item.category, quantity=item.quantity, location=item.location, available=item.quantity-active_count(db, item.id))

def loan_view(db, loan):
    state = "Returned" if loan.returned_at else ("Overdue" if utc(loan.due_at) < datetime.now(timezone.utc) else "Active")
    return LoanOutput(id=loan.id, equipment_id=loan.equipment_id, equipment_name=db.get(Equipment, loan.equipment_id).name, borrower=loan.borrower, due_at=loan.due_at, created_at=loan.created_at, returned_at=loan.returned_at, status=state)

@app.middleware("http")
async def observe(request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = route.path if route else "unmatched"
        if path not in ("/metrics", "/health", "/ready"):
            requests.labels(request.method, path, str(status)).inc()
            latency.labels(request.method, path).observe(time.perf_counter()-start)
        logger.info("method=%s route=%s status=%s duration=%.4f", request.method, path, status, time.perf_counter()-start)

@app.get("/health")
def health():
    return {"status": "UP"}

@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db.execute(select(Equipment.id).limit(1))
    except Exception:
        raise HTTPException(503, "Database or migrations unavailable") from None
    return {"status": "READY"}

@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

@app.get("/api/equipment", response_model=list[EquipmentOutput])
def list_equipment(db: Session = Depends(get_db), search: str = Query(default="", max_length=120)):
    stmt = select(Equipment).order_by(Equipment.id.desc())
    if search:
        stmt = stmt.where(Equipment.name.ilike(f"%{search}%"))
    return [equipment_view(db, item) for item in db.scalars(stmt)]

@app.post("/api/equipment", response_model=EquipmentOutput, status_code=201)
def create_equipment(data: EquipmentInput, db: Session = Depends(get_db)):
    item = Equipment(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return equipment_view(db, item)

@app.put("/api/equipment/{item_id}", response_model=EquipmentOutput)
def update_equipment(item_id: int, data: EquipmentInput, db: Session = Depends(get_db)):
    item = db.scalar(select(Equipment).where(Equipment.id == item_id).with_for_update())
    if not item:
        raise HTTPException(404, "Equipment not found")
    if data.quantity < active_count(db, item.id):
        raise HTTPException(409, "Quantity cannot be below outstanding loans")
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return equipment_view(db, item)

@app.delete("/api/equipment/{item_id}", status_code=204)
def delete_equipment(item_id: int, db: Session = Depends(get_db)):
    item = db.scalar(select(Equipment).where(Equipment.id == item_id).with_for_update())
    if not item:
        raise HTTPException(404, "Equipment not found")
    if db.scalar(select(func.count()).select_from(Loan).where(Loan.equipment_id == item_id)):
        raise HTTPException(409, "Equipment with loan history must be retained")
    db.delete(item)
    db.commit()
    return Response(status_code=204)

@app.get("/api/loans", response_model=list[LoanOutput])
def list_loans(db: Session = Depends(get_db)):
    return [loan_view(db, loan) for loan in db.scalars(select(Loan).order_by(Loan.id.desc()))]

@app.post("/api/loans", response_model=LoanOutput, status_code=201)
def borrow(data: LoanInput, db: Session = Depends(get_db)):
    if data.due_at <= datetime.now(timezone.utc):
        raise HTTPException(422, "Due date must be in the future")
    item = db.scalar(select(Equipment).where(Equipment.id == data.equipment_id).with_for_update())
    if not item:
        raise HTTPException(404, "Equipment not found")
    if active_count(db, item.id) >= item.quantity:
        raise HTTPException(409, "No units available")
    loan = Loan(**data.model_dump())
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan_view(db, loan)

@app.put("/api/loans/{loan_id}/return", response_model=LoanOutput)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.scalar(select(Loan).where(Loan.id == loan_id).with_for_update())
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.returned_at:
        raise HTTPException(409, "Loan already returned")
    loan.returned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(loan)
    return loan_view(db, loan)

@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.coalesce(func.sum(Equipment.quantity), 0)))
    active = db.scalar(select(func.count()).select_from(Loan).where(Loan.returned_at.is_(None)))
    overdue = db.scalar(select(func.count()).select_from(Loan).where(Loan.returned_at.is_(None), Loan.due_at < datetime.now(timezone.utc)))
    return {"total_units": total, "available": total-active, "active_loans": active, "overdue": overdue}
