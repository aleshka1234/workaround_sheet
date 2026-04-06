from .db.session import SessionLocal


class SQLAlchemySessionMiddleware:
    """Одна сессия SQLAlchemy на HTTP-запрос."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.sa_session = SessionLocal()
        try:
            response = self.get_response(request)
            if 200 <= response.status_code < 400:
                request.sa_session.commit()
            else:
                request.sa_session.rollback()
        except Exception:
            request.sa_session.rollback()
            raise
        finally:
            request.sa_session.close()
        return response
