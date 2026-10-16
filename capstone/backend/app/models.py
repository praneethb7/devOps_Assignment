from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Equipment(Base):
    __tablename__ = "equipment"
    __table_args__ = (CheckConstraint("quantity > 0", name="positive_quantity"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(120))

class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (Index("ix_loans_equipment_returned", "equipment_id", "returned_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="RESTRICT"))
    borrower: Mapped[str] = mapped_column(String(120))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
