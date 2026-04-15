# from typing import Optional
# from sqlalchemy.orm import Session
#
# from db.models_sa import CachedUser, UserType
#
#
# def fetch_user_info_from_sso(sso_login: str) -> Optional[dict]:
#     """
#     Получает данные пользователя из SSO/Лотоса.
#     ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ЗАПРОС К ВАШЕМУ API!
#     """
#     # Заглушка для тестирования
#     # В реальности здесь будет запрос к API портала или БД Лотоса
#
#     if "student" in sso_login:
#         return {
#             "email": f"{sso_login}@pnu.edu.ru",
#             "first_name": "Иван",
#             "last_name": "Иванов",
#             "middle_name": "Иванович",
#             "user_type": "student",
#             "group": "ПИ-91",
#             "institute": "ИМФИ",
#             "department": None
#         }
#     elif "staff" in sso_login:
#         return {
#             "email": f"{sso_login}@pnu.edu.ru",
#             "first_name": "Петр",
#             "last_name": "Петров",
#             "middle_name": "Петрович",
#             "user_type": "staff",
#             "group": None,
#             "institute": None,
#             "department": "Библиотека"
#         }
#
#     return None