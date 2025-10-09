from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Deprecated: polling runner removed. Use webhook infrastructure instead.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'Polling mode is removed. Configure webhook and use management commands setwebhook / deletewebhook.'
        ))
