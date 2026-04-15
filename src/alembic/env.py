import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Добавляем src/ в PYTHONPATH
# alembic.ini лежит в src/, env.py в src/alembic/
src_path = str(Path(__file__).parent.parent)
sys.path.insert(0, src_path)

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

import django

django.setup()

# Импорт моделей SQLAlchemy
from db import Base
from db.session import get_database_url

# Импортируем ВСЕ модели, чтобы Alembic их увидел
# Используем абсолютный импорт от корня src/

import db.models_sa  # noqa: F401

# Конфигурация Alembic

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Фильтр: мигрируем только таблицы, начинающиеся с 'workaround_'.
    Игнорируем таблицы Django (auth_*, django_*).
    """
    if type_ == "table":
        # Мигрируем только наши таблицы
        return name.startswith("workaround_")
    return True


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
