from sqlalchemy.orm import Session

from workaround.constants import StatusChoices
from workaround.db.models_sa import (
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem,
)


def apply_debt_rules(item: ObhhodnoiListZaiavlenieItem) -> None:
    if item.debt:
        item.status = int(StatusChoices.DEBT)


def recalc_statement_result_status(
    session: Session, statement: ObhhodnoiListZaiavlenie
) -> None:
    items = list(statement.line_statuses)
    if not items:
        return
    total = len(items)
    signed = sum(1 for i in items if i.status == int(StatusChoices.SIGNED))
    new_status = (
        int(StatusChoices.SIGNED) if total == signed else int(StatusChoices.NOT_SIGNED)
    )
    if statement.result_status != new_status:
        statement.result_status = new_status
