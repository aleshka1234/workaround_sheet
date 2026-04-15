# from django.contrib.auth.models import User
# from django.utils.deprecation import MiddlewareMixin
#
#
# class RestoreUserMiddleware(MiddlewareMixin):
#     """Восстанавливает пользователя из сессии и устанавливает флаги."""
#
#     def process_request(self, request):
#         # Если пользователь уже авторизован — ничего не делаем
#         if hasattr(request, 'user') and request.user.is_authenticated:
#             return
#
#         user_id = request.session.get('_auth_user_id')
#         user_type = request.session.get('user_type')
#
#         if user_id and user_type:
#             # Создаём пользователя с правильными флагами
#             user = User(id=int(user_id))
#             user.username = request.session.get('_auth_user_username',
#                                                 f'user_{user_id}')
#
#             if user_type == 'staff':
#                 user.is_staff = True
#                 user.is_superuser = request.session.get('is_superuser', False)
#             else:
#                 user.is_staff = False
#                 user.is_superuser = False
#
#             # Устанавливаем пользователя в request
#             request.user = user
#             request._cached_user = user
#             print(
#                 f"🔄 User restored: {user.username}, type={user_type}, is_staff={user.is_staff}")