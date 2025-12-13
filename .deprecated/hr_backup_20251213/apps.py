from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hr'
    verbose_name = 'HR - Xodimlar Boshqaruvi'
    
    def ready(self):
        import apps.hr.signals  # noqa
