from enum import IntEnum


class StatusChoices(IntEnum):
    """Совпадает с миграцией workaround 0002."""

    SIGNED = 0
    NOT_SIGNED = 1
    DEBT = 2


STATUS_LABELS = {
    StatusChoices.SIGNED: "Подписано",
    StatusChoices.NOT_SIGNED: "Не подписано",
    StatusChoices.DEBT: "Долг",
}


def status_display(value: int) -> str:
    return STATUS_LABELS.get(value, str(value))
