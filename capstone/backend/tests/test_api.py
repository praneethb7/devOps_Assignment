from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.models import Loan

ITEM = {"name": "Canon camera", "category": "Electronics", "quantity": 1, "location": "Media lab"}

def item(client):
    response = client.post("/api/equipment", json=ITEM)
    assert response.status_code == 201
    return response.json()["id"]

def loan(client, equipment_id, **kwargs):
    return client.post("/api/loans", json={"equipment_id": equipment_id, "borrower": "Praneeth", "due_at": (datetime.now(timezone.utc)+timedelta(days=2)).isoformat(), **kwargs})

def test_health_and_ready(client):
    assert client.get("/health").json() == {"status": "UP"}
    assert client.get("/ready").status_code == 200

def test_equipment_lifecycle(client):
    id = item(client)
    assert client.get("/api/equipment").json()[0]["available"] == 1
    assert client.put(f"/api/equipment/{id}", json={**ITEM, "quantity": 3}).json()["available"] == 3
    assert client.delete(f"/api/equipment/{id}").status_code == 204
    assert client.get("/api/equipment").json() == []

def test_search(client):
    item(client)
    assert len(client.get("/api/equipment?search=canon").json()) == 1
    assert client.get("/api/equipment?search=missing").json() == []

def test_invalid_inventory(client):
    for invalid in ({"quantity": 0}, {"name": "  "}, {"category": "bad"}):
        assert client.post("/api/equipment", json={**ITEM, **invalid}).status_code == 422

def test_borrow_return_updates_availability(client):
    id = item(client)
    response = loan(client, id)
    assert response.status_code == 201
    loan_id = response.json()["id"]
    assert client.get("/api/stats").json() == {"total_units": 1, "available": 0, "active_loans": 1, "overdue": 0}
    assert client.put(f"/api/loans/{loan_id}/return").json()["status"] == "Returned"
    assert client.get("/api/stats").json()["available"] == 1

def test_prevent_overbooking(client):
    id = item(client)
    assert loan(client, id).status_code == 201
    assert loan(client, id).status_code == 409

def test_reject_past_due_date(client):
    assert loan(client, item(client), due_at="2020-01-01T00:00:00Z").status_code == 422

def test_require_timezone(client):
    assert loan(client, item(client), due_at="2030-01-01T00:00:00").status_code == 422

def test_return_twice_is_conflict(client):
    id = loan(client, item(client)).json()["id"]
    assert client.put(f"/api/loans/{id}/return").status_code == 200
    assert client.put(f"/api/loans/{id}/return").status_code == 409

def test_keep_loan_history(client):
    id = item(client)
    loan_id = loan(client, id).json()["id"]
    assert client.delete(f"/api/equipment/{id}").status_code == 409
    client.put(f"/api/loans/{loan_id}/return")
    assert client.delete(f"/api/equipment/{id}").status_code == 409

def test_cannot_reduce_below_borrowed_quantity(client):
    id = item(client)
    client.put(f"/api/equipment/{id}", json={**ITEM, "quantity": 2})
    loan(client, id)
    loan(client, id)
    assert client.put(f"/api/equipment/{id}", json=ITEM).status_code == 409

def test_missing_resources(client):
    assert client.put("/api/equipment/999", json=ITEM).status_code == 404
    assert client.delete("/api/equipment/999").status_code == 404
    assert client.put("/api/loans/999/return").status_code == 404
    assert loan(client, 999).status_code == 404

def test_overdue_status(client, db):
    loan(client, item(client))
    record = db.scalar(select(Loan))
    record.due_at = datetime.now(timezone.utc)-timedelta(days=1)
    db.commit()
    assert client.get("/api/loans").json()[0]["status"] == "Overdue"
    assert client.get("/api/stats").json()["overdue"] == 1

def test_metrics(client):
    client.get("/api/stats")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert 'campuscrate_http_requests_total{method="GET",route="/api/stats",status="200"}' in response.text

def test_readiness_failure(client, db, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("database unavailable")
    monkeypatch.setattr(db, "execute", fail)
    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200
