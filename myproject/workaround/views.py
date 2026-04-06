from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView
# Импортируем твои модели и те самые StatusChoices из models.py
from .models import ObhhodnoiListZaiavlenie, ObhhodnoiListZaiavlenieItem, \
    StatusChoices


# 1. Интерфейс СОТРУДНИКА (Список всех заявок по его отделу)
class StaffWorkerView(ListView):
    model = ObhhodnoiListZaiavlenieItem
    template_name = 'obhhodnoi/staff_list.html'
    context_object_name = 'items'

    def get_queryset(self):
        # Позже здесь будет фильтрация по отделу сотрудника
        return ObhhodnoiListZaiavlenieItem.objects.all()

    def post(self, request, *args, **kwargs):
        # Кнопка «Подписать всем, у кого нет долгов»
        if 'sign_all_clean' in request.POST:
            # Берем только те пункты, где флаг debt=False и статус еще "Не подписано"
            items_to_update = ObhhodnoiListZaiavlenieItem.objects.filter(
                debt=False,
                status=StatusChoices.NOT_SIGNED
            )
            for item in items_to_update:
                item.status = StatusChoices.SIGNED
                item.save()  # Вызываем save(), чтобы сработал пересчет в модели
        return redirect('staff_list')


# 2. Обработка КНОПОК действий сотрудника
class ItemActionView(View):
    def post(self, request, pk):
        # Находим конкретную строку в обходном листе
        item = get_object_or_404(ObhhodnoiListZaiavlenieItem, pk=pk)
        action = request.POST.get('action')

        if action == 'sign':
            # Кнопка «Подписать»
            item.status = StatusChoices.SIGNED

        elif action == 'comment':
            # Кнопка «Отправить комментарий»5
            # Записываем текст и ставим статус "Долг", чтобы студент увидел проблему
            item.debt_comment = request.POST.get('comment_text')
            item.status = StatusChoices.DEBT
            item.debt = True  # Помечаем, что долг есть физически

        # Сохраняем изменения. Метод save() в твоем models.py сам
        # обновит result_status у главного заявления.
        item.save()
        return redirect('staff_list')


# 3. Интерфейс СТУДЕНТА (Просмотр своего обходного листа)
class StudentObhhodnoiDetailView(DetailView):
    model = ObhhodnoiListZaiavlenie
    template_name = 'obhhodnoi/student_detail.html'
    context_object_name = 'zaiavlenie'
    # Студент видит статус как для каждого отдела, так и для всего листа [cite: 55]
