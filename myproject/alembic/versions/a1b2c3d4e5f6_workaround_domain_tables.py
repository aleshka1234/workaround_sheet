"""Workaround domain tables (SQLAlchemy).

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-04-06

Создаёт только таблицы workaround_* (Django-системные таблицы не трогает).
Если таблицы уже есть (после старых миграций Django), шаги пропускаются.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    bool_false = sa.text("false") if is_pg else sa.text("0")
    ts_default = sa.text("CURRENT_TIMESTAMP")

    if not _table_exists("workaround_student"):
        op.create_table(
            "workaround_student",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "full_name",
                sa.String(length=255),
                nullable=False,
                server_default="",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("workaround_staffworker"):
        op.create_table(
            "workaround_staffworker",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "full_name",
                sa.String(length=255),
                nullable=False,
                server_default="",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("workaround_obhhodnoilistzaiavlenie"):
        op.create_table(
            "workaround_obhhodnoilistzaiavlenie",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("result_status", sa.Integer(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(
                ["student_id"],
                ["workaround_student.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("workaround_obhhodnoilistzaiavlenieitem"):
        op.create_table(
            "workaround_obhhodnoilistzaiavlenieitem",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("debt", sa.Boolean(), nullable=False, server_default=bool_false),
            sa.Column("debt_comment", sa.Text(), nullable=True),
            sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
            sa.Column(
                "date",
                sa.DateTime(timezone=True) if is_pg else sa.DateTime(),
                server_default=ts_default,
                nullable=False,
            ),
            sa.Column("statement_id", sa.Integer(), nullable=False),
            sa.Column("staff_worker_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["statement_id"],
                ["workaround_obhhodnoilistzaiavlenie.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["staff_worker_id"],
                ["workaround_staffworker.id"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    if _table_exists("workaround_obhhodnoilistzaiavlenieitem"):
        op.drop_table("workaround_obhhodnoilistzaiavlenieitem")
    if _table_exists("workaround_obhhodnoilistzaiavlenie"):
        op.drop_table("workaround_obhhodnoilistzaiavlenie")
    if _table_exists("workaround_staffworker"):
        op.drop_table("workaround_staffworker")
    if _table_exists("workaround_student"):
        op.drop_table("workaround_student")
