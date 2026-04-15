from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Отключаем автообновление last_login через Django ORM
        from django.contrib.auth import user_logged_in

        def dummy_update_last_login(sender, user, request, **kwargs):
            pass

        user_logged_in.disconnect(dispatch_uid='update_last_login')