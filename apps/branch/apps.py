from django.apps import AppConfig


class BranchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.branch'
    verbose_name = 'Filiallar'
    
    def ready(self):
        """Import signals when app is ready."""
        from . import signals  # noqa