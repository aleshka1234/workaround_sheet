from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, \
    func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

from enum import IntEnum, Enum


class StatusChoices(IntEnum):
    """Enum для статуса заявления"""

    SIGNED = 0 # Подписано
    NOT_SIGNED = 1 # Не подписано
    REFUSED = 2 # Отказано
    DEBT = 3 # Долг


STATUS_LABELS = {
    StatusChoices.SIGNED: "Подписано",
    StatusChoices.NOT_SIGNED: "Не подписано",
    StatusChoices.REFUSED: "Отказано",
    StatusChoices.DEBT: "Долг",
}


class Student(Base):
    """
    Модель студента

    Представляет таблицу "workaround_student" в базе данных.
    Содержит основную информацию о студенте и связи с его заявлениями.
    """
    __tablename__ = "workaround_student"

    # Уникальный идентификатор студента (первичный ключ)
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)

    # Полное имя студента (максимум 255 символов)
    full_name: Mapped[str] = mapped_column(String(255), default="",
                                           server_default="")

    # Связь с заявлениями студента (один ко многим)
    # При удалении студента все его заявления также удаляются (каскадное удаление)
    statements: Mapped[List["ObhhodnoiListZaiavlenie"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    # === ПОЛЯ ДЛЯ SSO ===
    sso_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Для обычной авторизации (временно, для тестов)
    username: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )


class Department(Base):
    """
    Модель отдела

    Представляет таблицу "workaround_department" в базе данных.
    Используется для хранения информации об отделах, через которые проходит обходной лист
    (например: Библиотека, Деканат, Бухгалтерия и т.д.).
    """
    __tablename__ = "workaround_department"

    # Уникальный идентификатор отдела (первичный ключ)
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)

    # Название отдела (уникальное, обязательное поле)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Связи с другими моделями

    # Сотрудники, работающие в этом отделе (один ко многим)
    staff_workers: Mapped[List["StaffWorker"]] = relationship(
        back_populates="department")

    # Пункты обходного листа, относящиеся к этому отделу (один ко многим)
    items: Mapped[List["ObhhodnoiListZaiavlenieItem"]] = relationship(
        back_populates="department")


class StaffWorker(Base):
    """
    Модель сотрудника

    Представляет таблицу "workaround_staffworker" в базе данных.
    Сотрудник работает в определенном отделе и может подписывать пункты обходного листа.
    """
    __tablename__ = "workaround_staffworker"

    # Уникальный идентификатор сотрудника (первичный ключ)
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)

    # Полное имя сотрудника (максимум 255 символов)
    full_name: Mapped[str] = mapped_column(String(255), default="",
                                           server_default="")

    # Внешний ключ к отделу, в котором работает сотрудник
    # При удалении отдела сотрудник также удаляется (каскадное удаление)
    department_id: Mapped["Department"] = mapped_column(
        ForeignKey("workaround_department.id", ondelete="CASCADE"),
        nullable=False
    )

    # Обратная связь с моделью Department
    # Позволяет получить доступ к информации об отделе сотрудника

    # === ПОЛЯ ДЛЯ SSO ===
    sso_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Для обычной авторизации (временно, для тестов)
    username: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    department: Mapped["Department"] = relationship(
        back_populates="staff_workers")

    # Флаг для входа в админку
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)


class ObhhodnoiListZaiavlenie(Base):
    """
    Модель заявления (шапка обходного листа)

    Представляет таблицу "workaround_obhhodnoilistzaiavlenie" в базе данных.
    Содержит основную информацию о заявлении студента и его итоговый статус.
    Является "родительской" сущностью для пунктов обходного листа.
    """
    __tablename__ = "workaround_obhhodnoilistzaiavlenie"

    # Уникальный идентификатор заявления (первичный ключ)
    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)

    # Внешний ключ к студенту, подавшему заявление
    # При удалении студента все его заявления также удаляются (каскадное удаление)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_student.id", ondelete="CASCADE"), nullable=False
    )

    # Итоговый статус заявления (SIGNED/NOT_SIGNED)
    # По умолчанию устанавливается в NOT_SIGNED
    result_status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=int(StatusChoices.NOT_SIGNED),
        server_default="1"
    )

    # Обратная связь с моделью Student
    # Позволяет получить доступ к информации о студенте
    student: Mapped[Student] = relationship(back_populates="statements")

    # Связь с пунктами заявления (строками обходного листа)
    # При удалении заявления все его пункты также удаляются (каскадное удаление)
    # Пункты упорядочены по дате создания
    line_statuses: Mapped[List["ObhhodnoiListZaiavlenieItem"]] = relationship(
        back_populates="statement",
        cascade="all, delete-orphan",
        order_by="ObhhodnoiListZaiavlenieItem.date",
    )

    def get_result_status_display(self) -> str:
        """
        Возвращает текстовое представление итогового статуса заявления.

        Returns:
            str: Текстовое описание статуса (например, "Подписано", "Не подписано")
                 или строковое представление числового кода статуса
        """
        return STATUS_LABELS.get(self.result_status, str(self.result_status))


class ObhhodnoiListZaiavlenieItem(Base):
    """Конкретная строка в обходном листе (Пункт из ТЗ)"""
    __tablename__ = "workaround_obhhodnoilistzaiavlenieitem"

    id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                    autoincrement=True)
    debt: Mapped[bool] = mapped_column(Boolean, default=False,
                                       server_default="0")
    debt_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=int(StatusChoices.NOT_SIGNED),
        server_default="1"
    )
    date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,  # Разрешаем базе хранить NULL
        default=None,  # По умолчанию в Python — None
        server_default=None  # Убираем автоматическую вставку даты базой
    )

    # Связь с заявлением
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_obhhodnoilistzaiavlenie.id",
                   ondelete="CASCADE"), nullable=False
    )

    # НОВОЕ: Чей это пункт (для фильтрации по отделам)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("workaround_department.id", ondelete="CASCADE"),
        nullable=False
    )

    # Кто фактически поставил подпись (может быть пустым, пока не подписано)
    staff_worker_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workaround_staffworker.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    statement: Mapped[ObhhodnoiListZaiavlenie] = relationship(
        back_populates="line_statuses")
    department: Mapped[Department] = relationship(back_populates="items")
    staff_worker: Mapped[Optional[StaffWorker]] = relationship()

    def get_status_display(self) -> str:
        return STATUS_LABELS.get(self.status, str(self.status))
