from django.urls import path
# Точка перед views означает "ищи в текущей папке"
from .views import StaffWorkerView, ItemActionView, \
    StudentPrintView, StudentCreateStatementView

urlpatterns = [
    path('staff/', StaffWorkerView.as_view(), name='staff_list'),
    # pk — это ID конкретной строки, которую мы подписываем
    path('item/<int:pk>/action/', ItemActionView.as_view(),
         name='item_action'),

    # # Путь для студента (п. 53-55 ТЗ)
    # path('student/<int:pk>/', StudentObhhodnoiDetailView.as_view(),
    #      name='student_detail'),
    path('statement/create/', StudentCreateStatementView.as_view(),
         name='create_statement'),

    path('student/<int:pk>/print/', StudentPrintView.as_view(),
         name='student_print'),

]
