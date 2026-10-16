"""Optional, idempotent sample data for local demonstrations only."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from .database import SessionLocal
from .models import Equipment, Loan

with SessionLocal() as db:
    if db.scalar(select(Equipment.id).limit(1)) is not None:
        print("Inventory is not empty; no sample data added.")
    else:
        samples = [
            ("Canon EOS 200D", "Electronics", 4, "Media lab"),
            ("Cricket kit", "Sports", 3, "Sports office"),
            ("Arduino starter kit", "Lab", 8, "Innovation lab"),
            ("Portable projector", "Events", 2, "Resource center"),
            ("Wireless microphone", "Events", 6, "AV room"),
            ("Logitech webcam", "Electronics", 5, "Media lab"),
        ]
        items = [Equipment(name=n, category=c, quantity=q, location=l) for n,c,q,l in samples]
        db.add_all(items)
        db.flush()
        now = datetime.now(timezone.utc)
        for i,(borrower,due,returned) in enumerate([("Praneeth Budati",2,False),("Student 102",3,False),("Student 118",-1,False),("Student 204",1,True)]):
            db.add(Loan(equipment_id=items[i].id, borrower=borrower, due_at=now+timedelta(days=due), created_at=now-timedelta(days=2), returned_at=now if returned else None))
        db.commit()
        print("Added six equipment types and four sample loans (including one overdue).")
