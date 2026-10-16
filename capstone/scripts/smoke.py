"""Verify a real deployed stack using only the Python standard library."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
def request(path, method="GET", data=None):
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(base+path, data=body, method=method, headers={"Content-Type": "application/json", **({"Host": os.environ["HOST_HEADER"]} if "HOST_HEADER" in os.environ else {})}), timeout=15) as response:
        result = response.read()
        return json.loads(result) if result else None

item = request("/api/equipment", "POST", {"name": "Smoke-test camera", "category": "Electronics", "quantity": 1, "location": "CI lab"})
assert item["available"] == 1
loan = request("/api/loans", "POST", {"equipment_id": item["id"], "borrower": "Integration check", "due_at": (datetime.now(timezone.utc)+timedelta(days=1)).isoformat()})
assert loan["status"] == "Active"
assert request(f"/api/loans/{loan['id']}/return", "PUT")["status"] == "Returned"
updated = request(f"/api/equipment/{item['id']}", "PUT", {"name": "Smoke-test camera", "category": "Electronics", "quantity": 2, "location": "CI lab"})
assert updated["available"] == 2
assert request("/api/stats")["available"] >= 2
assert any(row["id"] == item["id"] and row["available"] == 2 for row in request("/api/equipment"))
disposable = request("/api/equipment", "POST", {"name": "Disposable smoke fixture", "category": "Lab", "quantity": 1, "location": "CI lab"})
request(f"/api/equipment/{disposable['id']}", "DELETE")
assert not any(row["id"] == disposable["id"] for row in request("/api/equipment"))
print("PASS: create, borrow, return, update, list, delete and aggregate through frontend proxy")
