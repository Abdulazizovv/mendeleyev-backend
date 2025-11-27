from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.school.finance'
    verbose_name = 'Moliya'
    
    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa

