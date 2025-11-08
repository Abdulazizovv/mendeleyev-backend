from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth.profiles'

    def ready(self):
        import auth.profiles.signals  # noqa
