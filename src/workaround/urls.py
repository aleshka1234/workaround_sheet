from django.urls import path
from .views import StaffWorkerView, ItemActionView, \
    StudentPrintView, StudentCreateStatementView, index, \
    StudentPrintOfficialView, logout_view

urlpatterns = [
    path('', index, name='index'),  # ← главная с редиректом

    # Сотрудники
    path('staff/', StaffWorkerView.as_view(), name='staff_list'),
    path('item/<int:pk>/action/', ItemActionView.as_view(),
         name='item_action'),

    # Студенты
    path('statement/create/', StudentCreateStatementView.as_view(),
         name='create_statement'),
    path('student/<int:pk>/print/', StudentPrintView.as_view(),
         name='student_print'),
    path('student/<int:pk>/print/official/',
         StudentPrintOfficialView.as_view(), name='student_print_official'),
    # Маршрут для кнопки выхода
    path('logout/', logout_view, name='custom_logout'),

]
