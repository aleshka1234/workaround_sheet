# myproject — обходной лист (Django + SQLAlchemy + Alembic)

Доменные таблицы (`Student`, `ObhhodnoiListZaiavlenie`, …) описаны в **SQLAlchemy** (`workaround/db/models_sa.py`), схема БД ведётся **Alembic**.  
Django используется для HTTP, шаблонов и встроенной авторизации; системные таблицы (`auth_*`, `django_*`) создаются через `manage.py migrate`.

**База данных по умолчанию — PostgreSQL** (и у Django, и у SQLAlchemy).

## Установка

```bash
cd myproject
pip install -r requirements.txt
```

## PostgreSQL

Переменные окружения (имеют разумные дефолты `myproject` / `127.0.0.1` / `5432`):

| Переменная | Назначение |
|------------|------------|
| `POSTGRES_DB` | имя БД |
| `POSTGRES_USER` | пользователь |
| `POSTGRES_PASSWORD` | пароль |
| `POSTGRES_HOST` | хост |
| `POSTGRES_PORT` | порт |

Опционально полный URL только для SQLAlchemy/Alembic:

- `SQLALCHEMY_DATABASE_URI` — например `postgresql+psycopg://user:pass@host:5432/dbname`

Пример через Docker:

```bash
docker run --name myproject-postgres -e POSTGRES_DB=myproject -e POSTGRES_USER=myproject -e POSTGRES_PASSWORD=myproject -p 5432:5432 -d postgres:16
```

## Миграции

1. **Django** (системные таблицы + `workaround.0003` — снятие доменных моделей из состояния Django):

```bash
python manage.py migrate
```

2. **Alembic** (таблицы `workaround_*`):

```bash
python -m alembic upgrade head
```

Если таблицы `workaround_*` уже были созданы старыми миграциями Django в **SQLite**, а вы перешли на **PostgreSQL**, выполните `upgrade` на новой пустой БД Postgres (данные из SQLite нужно переносить отдельно).

## Запуск

```bash
python manage.py runserver
```

Дополнительно:

- `SQLALCHEMY_ECHO=1` — лог SQL в консоль.
- `ALLOWED_HOSTS` — через запятую (по умолчанию `127.0.0.1,localhost`).
