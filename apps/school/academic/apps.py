"""Academic app configuration."""
from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.school.academic'
    verbose_name = 'Akademik'
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.school.academic.signals  # noqa
