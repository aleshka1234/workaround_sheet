import os

from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    return getattr(
        settings,
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("SQLALCHEMY_DATABASE_URI", ""),
    )


engine = create_engine(
    get_database_url(),
    echo=getattr(settings, "SQLALCHEMY_ECHO", False),
    future=True,

    # --- НАСТРОЙКИ ПУЛА СОЕДИНЕНИЙ ДЛЯ HIGH-LOAD ---
    pool_size=20,  # Держим 20 соединений всегда открытыми и готовыми к работе
    max_overflow=20,# Разрешаем открыть еще 20 дополнительных при пиковой нагрузке (всего 40)
    pool_timeout=30,# Ждем максимум 30 секунд свободного соединения (чтобы не "вешать" сервер бесконечно)
    pool_recycle=1800,# Перезапускаем соединения каждые 30 минут (спасает от ошибки "MySQL server has gone away")
    pool_pre_ping=True,# Делаем быстрый ping перед запросом, чтобы убедиться, что БД не разорвала связь
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
