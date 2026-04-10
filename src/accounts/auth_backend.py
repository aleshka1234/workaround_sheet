from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from db.session import SessionLocal
from db.models_sa import CachedUser, UserType


class SSOCachedBackend(BaseBackend):
    """
    Аутентификация через SSO с кэшированием пользователя в SQLAlchemy.
    """

    def authenticate(self, request, remote_user=None):
        if not remote_user:
            return None

        db = SessionLocal()
        try:
            # Ищем или создаём пользователя в кэше
            cached_user = self._get_or_create_cached_user(db, remote_user)
            if not cached_user:
                return None

            # Создаём Django-пользователя в памяти
            django_user = User(
                username=cached_user.username,
                first_name=cached_user.first_name,
                last_name=cached_user.last_name,
                email=cached_user.email or "",
            )

            # Даём права на вход в админку, если сотрудник
            if cached_user.user_type == UserType.STAFF:
                django_user.is_staff = True

            # Здесь можно добавить назначение прав через self._assign_permissions()

            return django_user

        finally:
            db.close()

    def _get_or_create_cached_user(self, db, sso_login):
        """Находит или создаёт запись в кэше."""
        from db.logic import get_or_create_cached_user
        return get_or_create_cached_user(db, sso_login)

    def get_user(self, user_id):
        # Не используется, т.к. пользователь не хранится в Django DB
        return None
