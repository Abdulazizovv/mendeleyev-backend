from django.apps import AppConfig


class SchoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.school'
    verbose_name = 'Maktab Moduli'
    
    def ready(self):
        """Import admin modules when app is ready."""
        # Import admin to ensure models are registered
        from . import admin  # noqa

