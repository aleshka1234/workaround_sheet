from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from sqlalchemy.sql import func

from db import SessionLocal, Student, StaffWorker


class WorkaroundAuthBackend(BaseBackend):
    """
    Аутентификация через таблицы Student и StaffWorker.
    """

    def authenticate(self, request, username=None, password=None):
        if not username or not password:
            return None

        db = SessionLocal()

        try:
            user_data = db.query(Student).filter(
                Student.username == username).first()
            user_type = 'student'

            if user_data is None:
                user_data = db.query(StaffWorker).filter(
                    StaffWorker.username == username).first()
                user_type = 'staff'

            if user_data is None:
                return None

            # Проверка пароля
            if user_data.password_hash:
                if not check_password(password, user_data.password_hash):
                    return None

            else:
                # Если пароль не задан – для теста пропускаем (временно)
                pass

            # Обновляем last_login
            user_data.last_login = func.now()
            db.commit()

            # Разбираем full_name
            full_name = user_data.full_name or ""
            name_parts = full_name.split()
            first_name = name_parts[1] if len(name_parts) > 1 else ""
            last_name = name_parts[0] if name_parts else ""

            # Создаём Django-пользователя (в памяти, не сохраняем)
            django_user = User(
                id=user_data.id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=getattr(user_data, 'email', '') or "",
            )

            # Права
            if user_type == 'staff':
                django_user.is_staff = getattr(user_data, 'is_staff', False)
                django_user.is_superuser = getattr(user_data, 'is_superuser', False)
            else:
                django_user.is_staff = False
                django_user.is_superuser = False

            # Сохраняем дополнительные данные в сессии
            request.session['user_type'] = user_type
            request.session['user_db_id'] = user_data.id
            if user_type == 'staff':
                request.session['department_id'] = user_data.department_id

            return django_user

        except Exception:
            db.rollback()
            return None
        finally:
            db.close()

    def get_user(self, user_id):
        from django.contrib.auth.models import User
        from db import SessionLocal, Student, StaffWorker

        db = SessionLocal()
        try:
            # Ищем студента
            student = db.query(Student).get(user_id)
            if student:
                user = User(id=student.id, username=student.username)
                user.is_staff = False
                user.email = student.email or ""
                return user

            # Ищем сотрудника
            staff = db.query(StaffWorker).get(user_id)
            if staff:
                user = User(id=staff.id, username=staff.username)
                user.is_staff = staff.is_staff
                user.is_superuser = staff.is_superuser
                user.email = staff.email or ""
                return user

            return None
        finally:
            db.close()
