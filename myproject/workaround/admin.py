from django.contrib import admin
from .models import (
    Student,
    StaffWorker,
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem
)


# Настройка отображения пунктов внутри заявления
class ObhhodnoiListZaiavlenieItemInline(admin.TabularInline):
    model = ObhhodnoiListZaiavlenieItem
    extra = 0  # Не добавлять пустые строки по умолчанию
    fields = ('staff_worker', 'debt', 'status', 'debt_comment', 'date')
    readonly_fields = ('date',)  # Дату менять вручную нельзя
    show_change_link = True  # Ссылка на отдельную страницу пункта, если нужно


@admin.register(ObhhodnoiListZaiavlenie)
class ObhhodnoiListZaiavlenieAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'result_status')
    list_filter = ('result_status',)
    search_fields = ('student__full_name', 'id')

    # Очень важно: результат вычисляется автоматически,
    # поэтому запрещаем редактировать его вручную в админке
    readonly_fields = ('result_status',)

    inlines = [ObhhodnoiListZaiavlenieItemInline]


@admin.register(ObhhodnoiListZaiavlenieItem)
class ObhhodnoiListZaiavlenieItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'statement', 'staff_worker', 'status', 'debt',
                    'date')
    list_filter = ('status', 'debt', 'date')
    readonly_fields = ('date',)


# Регистрация вспомогательных таблиц
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name')


@admin.register(StaffWorker)
class StaffWorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name')
