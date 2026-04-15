from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.utils import timezone
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from django.contrib.auth.decorators import login_required  # для функций
from django.contrib.admin.views.decorators import \
    staff_member_required  # для админ-доступа
from django.utils.decorators import method_decorator  # для классов (CBV)

from workaround.decorators import staff_required

from db import StatusChoices
from db.logic import apply_debt_rules, \
    recalc_statement_result_status, initialize_statement_items
from db.models_sa import (
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem,
    StaffWorker,
    Student
)


def _session(request: HttpRequest):
    # Предполагаем, что сессия прокидывается через middleware
    return request.sa_session


@login_required
def index(request):
    """Главная страница — перенаправляет в зависимости от роли."""
    user_type = request.session.get('user_type')

    if user_type == 'student':
        # Перенаправляем на страницу студента
        # pk берём из сессии (user_db_id)
        student_id = request.session.get('user_db_id')

        # Проверяем, есть ли у студента заявление
        session = _session(request)
        statement = session.query(ObhhodnoiListZaiavlenie).filter(
            ObhhodnoiListZaiavlenie.student_id == student_id
        ).first()

        if statement:
            # Заявление есть → показываем его
            return redirect('student_print', pk=statement.id)
        else:
            # Заявления нет → на страницу создания
            return redirect('create_statement')

    elif user_type == 'staff':
        # Перенаправляем на панель сотрудника
        return redirect('staff_list')
    else:
        # На всякий случай — выход
        return redirect('logout')


@method_decorator(login_required, name='dispatch')
class StaffWorkerView(View):
    """Список заявлений для сотрудника конкретного отдела (ТЗ п. 12, 17)"""
    template_name = "obhhodnoi/staff_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Доп. проверка: только сотрудники
        if request.session.get('user_type') != 'staff':
            return HttpResponse("Доступ запрещён", status=403)

        return super().dispatch(request, *args, **kwargs)

    def get_current_worker(self, session, request):
        """Возвращает сотрудника, соответствующего авторизованному пользователю."""
        # Получаем ID авторизованного сотрудника
        staff_id = request.session.get('user_db_id')

        if not staff_id:
            return None

        # Ищем сотрудника по ID
        return session.get(StaffWorker, staff_id)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        session = _session(request)
        worker = self.get_current_worker(session, request)

        if not worker:
            return HttpResponse(
                "Ошибка: Вы не зарегистрированы как сотрудник подразделения.",
                status=403)

        # Получаем параметры из URL (например: ?q=Иванов&status=1)
        search_query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '')

        # Строим базовый запрос
        stmt = (
            select(ObhhodnoiListZaiavlenieItem)
            .join(ObhhodnoiListZaiavlenieItem.statement)
            .join(
                ObhhodnoiListZaiavlenie.student)  # Явный join для поиска по ФИО
            .options(
                joinedload(ObhhodnoiListZaiavlenieItem.statement).joinedload(
                    ObhhodnoiListZaiavlenie.student),
                joinedload(ObhhodnoiListZaiavlenieItem.department)
            )
            .where(
                ObhhodnoiListZaiavlenieItem.department_id == worker.department_id)
        )

        # Применяем ПОИСК по ФИО студента, если запрос не пустой
        if search_query:
            # icontains делает поиск независимым от регистра (Иванов == иванов)
            stmt = stmt.where(Student.full_name.icontains(search_query))

        # 4. Применяем ФИЛЬТР по статусу, если он выбран
        if status_filter and status_filter.isdigit():
            stmt = stmt.where(
                ObhhodnoiListZaiavlenieItem.status == int(status_filter))

        # 5. Сортируем и выполняем запрос
        stmt = stmt.order_by(ObhhodnoiListZaiavlenieItem.id.desc())  # desc() чтобы новые были сверху
        items = session.scalars(stmt).unique().all()

        return render(request, self.template_name, {
            "items": items,
            "worker": worker,
            "department": worker.department,
            # Передаем параметры обратно в шаблон, чтобы сохранить значения в полях
            "search_query": search_query,
            "status_filter": status_filter,
        })

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        session = _session(request)
        worker = self.get_current_worker(session, request)

        if "sign_all_clean" in request.POST:
            stmt = select(ObhhodnoiListZaiavlenieItem).where(
                ObhhodnoiListZaiavlenieItem.department_id == worker.department_id,
                ObhhodnoiListZaiavlenieItem.debt.is_(False),
                ObhhodnoiListZaiavlenieItem.status == int(
                    StatusChoices.NOT_SIGNED),
            )
            items = session.scalars(stmt).all()

            now = timezone.now()
            for item in items:
                item.status = int(StatusChoices.SIGNED)
                item.staff_worker_id = worker.id
                item.date = now  # Фиксируем время подписи

                apply_debt_rules(item)
                recalc_statement_result_status(session, item.statement)

            session.commit()

        return redirect("staff_list")


@method_decorator(staff_required, name='dispatch')
class ItemActionView(View):
    """Индивидуальные действия над пунктом (Подпись / Выставление долга)"""

    def get_current_worker(self, session, request):
        """Возвращает сотрудника, соответствующего авторизованному пользователю."""
        # Получаем ID авторизованного сотрудника
        staff_id = request.session['user_db_id']

        if not staff_id:
            return None

        # Ищем сотрудника по ID
        return session.get(StaffWorker, staff_id)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = _session(request)
        item = session.get(ObhhodnoiListZaiavlenieItem, pk)
        if item is None:
            raise Http404()

        # Получаем сотрудника, который совершает действие
        worker = self.get_current_worker(session, request)
        action = request.POST.get("action")

        if action == "sign":
            item.status = int(StatusChoices.SIGNED)
            item.debt = False
            item.debt_comment = None

        elif action == "refuse":
            item.status = int(StatusChoices.REFUSED)
            item.debt = True
            item.debt_comment = "В подписи отказано. Необходимо явиться в отдел очно."

        elif action == "comment":
            item.status = int(StatusChoices.DEBT)
            item.debt = True
            item.debt_comment = request.POST.get("comment_text")

        # Общие поля для любого действия
        item.staff_worker_id = worker.id
        item.date = timezone.now()

        apply_debt_rules(item)
        recalc_statement_result_status(session, item.statement)

        session.commit()
        return redirect("staff_list")


@method_decorator(login_required, name='dispatch')
class StudentPrintView(View):
    """Печать обходного листа - Приложение 1 (ТЗ п. 62)"""

    def dispatch(self, request, *args, **kwargs):
        # Проверяем, что пользователь — студент
        if request.session.get('user_type') != 'student':
            raise PermissionDenied('Доступ только для студентов')

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        session = _session(request)
        student_id = request.session.get('user_db_id')

        # Загружаем заявление
        query = (
            select(ObhhodnoiListZaiavlenie)
            .options(
                selectinload(ObhhodnoiListZaiavlenie.line_statuses)
                .joinedload(ObhhodnoiListZaiavlenieItem.department)
            )
            .filter(ObhhodnoiListZaiavlenie.id == pk)
        )
        statement = session.execute(query).unique().scalar_one_or_none()

        if not statement:
            return render(request, 'obhhodnoi/create_statement.html',
                          {'student_id': pk})

        if statement.student_id != student_id:
            raise PermissionDenied(
                "Вы можете просматривать только свой обходной лист.")

        return render(request, 'obhhodnoi/print_form.html',
                      {'statement': statement})


@method_decorator(login_required, name='dispatch')
class StudentPrintOfficialView(View):
    """Официальный бланк для печати."""

    def get(self, request, pk):
        session = _session(request)
        statement = session.query(ObhhodnoiListZaiavlenie).get(pk)

        if not statement:
            raise Http404()

        return render(request, 'obhhodnoi/student_print_official.html', {
            'statement': statement
        })


@method_decorator(login_required, name='dispatch')
class StudentCreateStatementView(View):
    """Создание обходного листа (студентом)"""
    template_name = "obhhodnoi/create_statement.html"

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('user_type') != 'student':
            raise PermissionDenied("Только студенты могут создавать заявления")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'obhhodnoi/create_statement.html')

    def post(self, request):
        session = _session(request)
        student_id = request.session.get(
            'user_db_id')  # ← реальный ID из сессии

        new_statement = ObhhodnoiListZaiavlenie(
            student_id=student_id,  # ✅ Реальный студент
            result_status=int(StatusChoices.NOT_SIGNED)
        )

        # flush() позволяет получить ID заявления, не закрывая транзакцию
        session.add(new_statement)
        session.flush()

        # 2. Магия: создаем все 10 пунктов для отделов
        initialize_statement_items(session, new_statement.id)

        session.commit()

        # Перенаправляем на страницу этого заявления (Приложение 1 или Detail)
        return redirect('student_print', pk=new_statement.id)
