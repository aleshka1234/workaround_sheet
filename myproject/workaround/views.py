from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from workaround.constants import StatusChoices
from workaround.db.logic import apply_debt_rules, \
    recalc_statement_result_status, initialize_statement_items
from workaround.db.models_sa import (
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem,
    StaffWorker,
    Department
)
from workaround.db.session import SessionLocal


def _session(request: HttpRequest):
    # Предполагаем, что сессия прокидывается через middleware
    return request.sa_session


class StaffWorkerView(View):
    """Список заявлений для сотрудника конкретного отдела (ТЗ п. 12, 17)"""
    template_name = "obhhodnoi/staff_list.html"

    def get_current_worker(self, session):
        # В реальной системе тут фильтр по request.user.id.
        # Для тестов берем первого попавшегося сотрудника.
        return session.scalar(select(StaffWorker).limit(1))

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        session = _session(request)
        worker = self.get_current_worker(session)

        if not worker:
            return HttpResponse(
                "Ошибка: Вы не зарегистрированы как сотрудник подразделения.",
                status=403)

        # Выбираем только те пункты, которые относятся к ОТДЕЛУ этого сотрудника
        stmt = (
            select(ObhhodnoiListZaiavlenieItem)
            .join(ObhhodnoiListZaiavlenieItem.statement)
            .options(
                joinedload(ObhhodnoiListZaiavlenieItem.statement).joinedload(
                    ObhhodnoiListZaiavlenie.student),
                joinedload(ObhhodnoiListZaiavlenieItem.department)
            )
            .where(
                ObhhodnoiListZaiavlenieItem.department_id == worker.department_id)
            .order_by(ObhhodnoiListZaiavlenieItem.id)
        )
        items = session.scalars(stmt).unique().all()

        return render(request, self.template_name, {
            "items": items,
            "worker": worker,
            "department": worker.department
        })

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        session = _session(request)
        worker = self.get_current_worker(session)

        if "sign_all_clean" in request.POST:
            # Массовая подпись только для своего отдела
            stmt = select(ObhhodnoiListZaiavlenieItem).where(
                ObhhodnoiListZaiavlenieItem.department_id == worker.department_id,
                ObhhodnoiListZaiavlenieItem.debt.is_(False),
                ObhhodnoiListZaiavlenieItem.status == int(
                    StatusChoices.NOT_SIGNED),
            )
            items = session.scalars(stmt).all()
            for item in items:
                item.status = int(StatusChoices.SIGNED)
                item.staff_worker_id = worker.id  # Фиксируем КТО подписал (ТЗ)
                apply_debt_rules(item)
                recalc_statement_result_status(session, item.statement)
            session.commit()

        return redirect("staff_list")


class ItemActionView(View):
    """Индивидуальные действия над пунктом (По  дпись / Выставление долга)"""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = _session(request)
        item = session.get(ObhhodnoiListZaiavlenieItem, pk)
        if item is None:
            raise Http404()

        # Получаем сотрудника, который совершает действие
        worker = session.scalar(select(StaffWorker).limit(1))
        action = request.POST.get("action")

        if action == "sign":
            item.status = int(StatusChoices.SIGNED)
            item.debt = False
            item.staff_worker_id = worker.id
        elif action == "comment":
            item.debt_comment = request.POST.get("comment_text")
            item.debt = True
            item.status = int(StatusChoices.DEBT)  # Статус "Долг"
            item.staff_worker_id = worker.id

        apply_debt_rules(item)
        recalc_statement_result_status(session, item.statement)
        session.commit()
        return redirect("staff_list")


class StudentPrintView(View):
    """Печать обходного листа - Приложение 1 (ТЗ п. 62)"""

    def get(self, request, pk):
        session = _session(request)

        # Загружаем всё дерево данных одним запросом (Eager Loading)
        query = (
            select(ObhhodnoiListZaiavlenie)
            .options(
                selectinload(ObhhodnoiListZaiavlenie.student),
                selectinload(ObhhodnoiListZaiavlenie.line_statuses).options(
                    selectinload(ObhhodnoiListZaiavlenieItem.department),
                    selectinload(ObhhodnoiListZaiavlenieItem.staff_worker)
                )
            )
            .filter(ObhhodnoiListZaiavlenie.id == pk)
        )

        result = session.execute(query).unique().scalar_one_or_none()

        if not result:
            raise Http404("Заявление не найдено")

        return render(request, 'obhhodnoi/print_form.html',
                      {'statement': result})


class StudentCreateStatementView(View):
    """Создание обходного листа (студентом)"""
    template_name = "obhhodnoi/create_statement.html"


    def get(self, request):
        # Просто показываем страницу с кнопкой "Подтвердить"
        return render(request, self.template_name)

    def post(self, request):
        session = _session(request)

        # 1. Создаем само заявление
        # В реальной жизни тут student_id = request.user.id
        new_statement = ObhhodnoiListZaiavlenie(
            student_id=1,  # Заглушка
            result_status=1  # Статус "В процессе"
        )
        session.add(new_statement)

        # flush() позволяет получить ID заявления, не закрывая транзакцию
        session.flush()

        # 2. Магия: создаем все 10 пунктов для отделов
        initialize_statement_items(session, new_statement.id)

        session.commit()

        # Перенаправляем на страницу этого заявления (Приложение 1 или Detail)
        return redirect('student_print', pk=new_statement.id)
