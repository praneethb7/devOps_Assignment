"""Create equipment inventory and loan ledger."""
from alembic import op
import sqlalchemy as sa
revision = "0001_equipment_loans"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("equipment", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("category", sa.String(40), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("location", sa.String(120), nullable=False), sa.CheckConstraint("quantity > 0", name="positive_quantity"))
    op.create_table("loans", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("equipment_id", sa.Integer(), sa.ForeignKey("equipment.id", ondelete="RESTRICT"), nullable=False), sa.Column("borrower", sa.String(120), nullable=False), sa.Column("due_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_loans_equipment_returned", "loans", ["equipment_id", "returned_at"])

def downgrade():
    op.drop_table("loans")
    op.drop_table("equipment")
