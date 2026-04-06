from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workaround.constants import STATUS_LABELS, StatusChoices
from workaround.db.base import Base


class Student(Base):
    __tablename__ = "workaround_student"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), default="", server_default="")

    statements: Mapped[List["ObhhodnoiListZaiavlenie"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )


class StaffWorker(Base):
    __tablename__ = "workaround_staffworker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), default="", server_default="")


class ObhhodnoiListZaiavlenie(Base):
    __tablename__ = "workaround_obhhodnoilistzaiavlenie"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_student.id", ondelete="CASCADE"), nullable=False
    )
    result_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=int(StatusChoices.NOT_SIGNED),
        server_default="1",
    )

    student: Mapped[Student] = relationship(back_populates="statements")
    line_statuses: Mapped[List["ObhhodnoiListZaiavlenieItem"]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan",
        order_by="ObhhodnoiListZaiavlenieItem.date",
    )

    def get_result_status_display(self) -> str:
        return STATUS_LABELS.get(self.result_status, str(self.result_status))


class ObhhodnoiListZaiavlenieItem(Base):
    __tablename__ = "workaround_obhhodnoilistzaiavlenieitem"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    debt: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    debt_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=int(StatusChoices.NOT_SIGNED),
        server_default="1",
    )
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_obhhodnoilistzaiavlenie.id", ondelete="CASCADE"),
        nullable=False,
    )
    staff_worker_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_staffworker.id", ondelete="CASCADE"),
        nullable=False,
    )

    statement: Mapped[ObhhodnoiListZaiavlenie] = relationship(
        back_populates="line_statuses"
    )
    staff_worker: Mapped[StaffWorker] = relationship()

    def get_status_display(self) -> str:
        return STATUS_LABELS.get(self.status, str(self.status))
