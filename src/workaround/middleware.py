from django.utils.functional import SimpleLazyObject, empty
from django.utils.cache import add_never_cache_headers
from db import SessionLocal

class SQLAlchemySessionMiddleware:
    """Ленивая сессия SQLAlchemy: создается только при первом реальном запросе к БД."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Назначаем "ленивый" объект. Подключение к БД НЕ происходит!
        request.sa_session = SimpleLazyObject(lambda: SessionLocal())

        try:
            response = self.get_response(request)

            # 2. Проверяем, обращались ли мы к базе во время обработки запроса во views.
            # Если _wrapped не равен empty, значит сессия была инициализирована.
            if getattr(request.sa_session, '_wrapped', empty) is not empty:
                if 200 <= response.status_code < 400:
                    request.sa_session.commit()
                else:
                    request.sa_session.rollback()

        except Exception:
            if getattr(request.sa_session, '_wrapped', empty) is not empty:
                request.sa_session.rollback()
            raise
        finally:
            # Закрываем сессию, только если она реально создавалась
            if getattr(request.sa_session, '_wrapped', empty) is not empty:
                request.sa_session.close()

        return response

class DisableBfCacheMiddleware:
    """
    Запрещает браузеру кэшировать страницы портала.
    Решает проблему призрачных сессий при нажатии кнопки 'Назад'.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Добавляем заголовки Cache-Control: max-age=0, no-cache, no-store, must-revalidate
        add_never_cache_headers(response)
        return response