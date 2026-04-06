from django.db import models
from django.utils import timezone


# Константы статусов
class StatusChoices(models.IntegerChoices):
    SIGNED = 0, 'Подписано'
    NOT_SIGNED = 1, 'Не подписано'
    DEBT = 2, 'Долг'


# Заглушки для будущей интеграции
class Student(models.Model):
    # Django создаст ID автоматически, если не указать другое
    full_name = models.CharField(max_length=255, verbose_name="ФИО Студента",
                                 blank=True)

    def __str__(self):
        return self.full_name


class StaffWorker(models.Model):
    full_name = models.CharField(max_length=255, verbose_name="ФИО Сотрудника",
                                 blank=True)

    def __str__(self):
        return self.full_name


class ObhhodnoiListZaiavlenie(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE,
                                verbose_name="Студент")
    result_status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_SIGNED,
        verbose_name='Общий статус'
    )

    def update_result_status(self):
        """Метод для пересчета общего статуса заявления"""
        # Берем все пункты через related_name='line_statuses'
        items = self.line_statuses.all()

        if items.exists():
            total_count = items.count()
            signed_count = items.filter(status=StatusChoices.SIGNED).count()

            # Если все пункты подписаны, ставим общий статус "Подписано"
            if total_count == signed_count:
                new_status = StatusChoices.SIGNED
            else:
                new_status = StatusChoices.NOT_SIGNED

            # Сохраняем только если статус действительно изменился
            if self.result_status != new_status:
                self.result_status = new_status
                # update_fields важен для производительности и избежания рекурсии
                self.save(update_fields=['result_status'])

    def __str__(self):
        return f'Заявление №{self.id} — {self.get_result_status_display()}'


class ObhhodnoiListZaiavlenieItem(models.Model):
    statement = models.ForeignKey(
        ObhhodnoiListZaiavlenie,
        on_delete=models.CASCADE,
        related_name='line_statuses'
    )
    debt = models.BooleanField(default=False, verbose_name="Долг")
    debt_comment = models.TextField(blank=True, null=True,
                                    verbose_name="Комментарий")
    status = models.IntegerField(
        choices=StatusChoices.choices,
        default=StatusChoices.NOT_SIGNED,
        verbose_name="Статус пункта"
    )
    staff_worker = models.ForeignKey(StaffWorker, on_delete=models.CASCADE,
                                     verbose_name="Сотрудник")

    # На схеме был datetime, поэтому используем DateTimeField
    date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Если стоит флаг долга, принудительно ставим статус пункта
        if self.debt:
            self.status = StatusChoices.DEBT

        super().save(*args, **kwargs)

        # Вызываем метод родителя (теперь имена совпадают)
        self.statement.update_result_status()

    def __str__(self):
        return f'Пункт заявления {self.statement_id} (статус: {self.get_status_display()})'
