from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from mailing.models import Mailing
from mailing.services import send_mailing_instance


class Command(BaseCommand):
    """Команда для отправки рассылки по ID через консоль."""

    help = "Использование: python manage.py send_mailing <mailing_id>"

    def add_arguments(self, parser):
        """Добавление аргумента — ID рассылки."""
        parser.add_argument("mailing_id", type=int)

    def handle(self, *args, **options):
        """Запуск рассылки с указанным ID."""
        mailing_id = options["mailing_id"]
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError("Рассылка с таким ID не найдена.")

        send_mailing_instance(mailing, settings.DEFAULT_FROM_EMAIL)
        self.stdout.write(self.style.SUCCESS(f"Mailing {mailing_id} отправлена."))
