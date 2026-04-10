from django.db import migrations


class Migration(migrations.Migration):
    """
    Убираем доменные модели из состояния Django без DROP таблиц.
    Дальше схему ведёт Alembic (workaround.db.models_sa).
    """

    dependencies = [
        ("workaround", "0002_alter_obhhodnoilistzaiavlenie_result_status_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="ObhhodnoiListZaiavlenieItem"),
                migrations.DeleteModel(name="ObhhodnoiListZaiavlenie"),
                migrations.DeleteModel(name="StaffWorker"),
                migrations.DeleteModel(name="Student"),
            ],
            database_operations=[],
        ),
    ]
