"""add_student_user_link

Revision ID: f7a8b9c0d1e2
Revises: e4f3a2b1c9d0
Create Date: 2026-04-27 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f7a8b9c0d1e2"
down_revision = "e4f3a2b1c9d0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("student", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_student_user_id", ["user_id"])
        batch_op.create_foreign_key("fk_student_user_id_user", "user", ["user_id"], ["id"])


def downgrade():
    with op.batch_alter_table("student", schema=None) as batch_op:
        batch_op.drop_constraint("fk_student_user_id_user", type_="foreignkey")
        batch_op.drop_constraint("uq_student_user_id", type_="unique")
        batch_op.drop_column("user_id")
