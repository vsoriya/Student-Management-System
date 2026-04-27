"""add_enrollments

Revision ID: e4f3a2b1c9d0
Revises: 8c049fab2653
Create Date: 2026-04-27 18:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e4f3a2b1c9d0"
down_revision = "8c049fab2653"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "enrollment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["class_rooms.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["student.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id"),
    )


def downgrade():
    op.drop_table("enrollment")
