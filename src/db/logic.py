from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models_sa import (
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem,
    Department,StatusChoices
)


def apply_debt_rules(item: ObhhodnoiListZaiavlenieItem) -> None:
    """
    Применяет бизнес-правила для обработки задолженности.

    Если у элемента есть задолженность (debt == True),
    устанавливаем статус "DEBT", независимо от текущего статуса.
    В противном случае статус не меняется — предполагается,
    что он уже был установлен корректно ранее.

    Args:
        item (ObhhodnoiListZaiavlenieItem): Пункт заявления для обработки
    """
    if item.debt:
        item.status = int(StatusChoices.DEBT)


def recalc_statement_result_status(
        session: Session, statement: ObhhodnoiListZaiavlenie
) -> None:
    """
    Пересчитывает итоговый статус заявления на основе статусов его пунктов.

    Args:
        session (Session): Сессия SQLAlchemy
        statement (ObhhodnoiListZaiavlenie): Заявление, для которого пересчитывается статус
    """
    # Получаем список всех строк (items) заявления
    items = list(statement.line_statuses)

    # Если нет ни одной строки — нечего пересчитывать, выходим
    if not items:
        return

    # Считаем общее количество строк
    total = len(items)

    # Считаем количество строк со статусом "SIGNED"
    signed = sum(1 for i in items if i.status == int(StatusChoices.SIGNED))

    # Определяем итоговый статус заявления:
    # Если все строки подписаны — всё заявление считается "SIGNED",
    # иначе — "NOT_SIGNED"
    new_status = (
        int(StatusChoices.SIGNED) if total == signed else int(
            StatusChoices.NOT_SIGNED)
    )

    # Обновляем итоговый статус заявления только если он изменился
    # Это помогает избежать лишних обновлений в БД
    if statement.result_status != new_status:
        statement.result_status = new_status


def initialize_statement_items(session, statement_id: int):
    """Находит все отделы в БД и создает пустые пункты для нового заявления"""
    # Получаем все доступные отделы
    departments = session.scalars(select(Department)).all()

    for dept in departments:
        new_item = ObhhodnoiListZaiavlenieItem(
            statement_id=statement_id,
            department_id=dept.id,
            status=1, # NOT_SIGNED (Не подписано)
            debt=False,
        )
        session.add(new_item)
        # Мы не делаем здесь commit(), сессия закоммитится во View

