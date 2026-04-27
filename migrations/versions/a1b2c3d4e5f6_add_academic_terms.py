"""add_academic_terms

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-04-27 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "academic_term",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("semester", sa.String(length=40), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("attendance", schema=None) as batch_op:
        batch_op.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_attendance_term_id_academic_term", "academic_term", ["term_id"], ["id"])
    with op.batch_alter_table("enrollment", schema=None) as batch_op:
        batch_op.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_enrollment_term_id_academic_term", "academic_term", ["term_id"], ["id"])
    with op.batch_alter_table("schedule", schema=None) as batch_op:
        batch_op.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_schedule_term_id_academic_term", "academic_term", ["term_id"], ["id"])
    with op.batch_alter_table("score", schema=None) as batch_op:
        batch_op.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_score_term_id_academic_term", "academic_term", ["term_id"], ["id"])


def downgrade():
    with op.batch_alter_table("score", schema=None) as batch_op:
        batch_op.drop_constraint("fk_score_term_id_academic_term", type_="foreignkey")
        batch_op.drop_column("term_id")
    with op.batch_alter_table("schedule", schema=None) as batch_op:
        batch_op.drop_constraint("fk_schedule_term_id_academic_term", type_="foreignkey")
        batch_op.drop_column("term_id")
    with op.batch_alter_table("enrollment", schema=None) as batch_op:
        batch_op.drop_constraint("fk_enrollment_term_id_academic_term", type_="foreignkey")
        batch_op.drop_column("term_id")
    with op.batch_alter_table("attendance", schema=None) as batch_op:
        batch_op.drop_constraint("fk_attendance_term_id_academic_term", type_="foreignkey")
        batch_op.drop_column("term_id")
    op.drop_table("academic_term")
