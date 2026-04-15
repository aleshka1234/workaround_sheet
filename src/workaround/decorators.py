from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def staff_required(view_func):
    """
    Декоратор для views, доступных только сотрудникам.
    В отличие от staff_member_required, редиректит на /accounts/login/
    и проверяет user_type в сессии.
    """
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('user_type') != 'staff':
            raise PermissionDenied("Доступ только для сотрудников")
        return view_func(request, *args, **kwargs)
    return _wrapped_view