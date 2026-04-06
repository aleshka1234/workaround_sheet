from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from workaround.constants import StatusChoices
from workaround.db.logic import apply_debt_rules, recalc_statement_result_status
from workaround.db.models_sa import (
    ObhhodnoiListZaiavlenie,
    ObhhodnoiListZaiavlenieItem,
)


def _session(request: HttpRequest):
    return request.sa_session


class StaffWorkerView(ListView):
    template_name = "obhhodnoi/staff_list.html"
    context_object_name = "items"

    def get_queryset(self):
        session = _session(self.request)
        stmt = (
            select(ObhhodnoiListZaiavlenieItem)
            .options(
                joinedload(ObhhodnoiListZaiavlenieItem.statement).joinedload(
                    ObhhodnoiListZaiavlenie.student
                ),
            )
            .order_by(ObhhodnoiListZaiavlenieItem.id)
        )
        return list(session.scalars(stmt).unique().all())

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if "sign_all_clean" in request.POST:
            session = _session(request)
            items = session.scalars(
                select(ObhhodnoiListZaiavlenieItem).where(
                    ObhhodnoiListZaiavlenieItem.debt.is_(False),
                    ObhhodnoiListZaiavlenieItem.status == int(StatusChoices.NOT_SIGNED),
                )
            ).all()
            for item in items:
                item.status = int(StatusChoices.SIGNED)
                apply_debt_rules(item)
                recalc_statement_result_status(session, item.statement)
        return redirect("staff_list")

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return self.render_to_response(context)


class ItemActionView(View):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = _session(request)
        item = session.get(ObhhodnoiListZaiavlenieItem, pk)
        if item is None:
            raise Http404()

        action = request.POST.get("action")

        if action == "sign":
            item.status = int(StatusChoices.SIGNED)
        elif action == "comment":
            item.debt_comment = request.POST.get("comment_text")
            item.debt = True

        apply_debt_rules(item)
        recalc_statement_result_status(session, item.statement)
        return redirect("staff_list")


class StudentObhhodnoiDetailView(View):
    template_name = "obhhodnoi/student_detail.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        session = _session(request)
        stmt = (
            select(ObhhodnoiListZaiavlenie)
            .where(ObhhodnoiListZaiavlenie.id == pk)
            .options(
                joinedload(ObhhodnoiListZaiavlenie.line_statuses).joinedload(
                    ObhhodnoiListZaiavlenieItem.staff_worker
                ),
            )
        )
        zaiavlenie = session.scalars(stmt).unique().one_or_none()
        if zaiavlenie is None:
            raise Http404()
        return render(
            request,
            self.template_name,
            {"zaiavlenie": zaiavlenie},
        )
