import logging

from django.core.mail import send_mail
from django.utils import timezone

from .models import MailAttempt, Mailing

logger = logging.getLogger(__name__)


def send_email_to_recipient(subject, body, recipient_email, from_email):
    """Отправляет письмо одному получателю и возвращает результат."""
    try:
        result = send_mail(subject, body, from_email, [recipient_email])
        status = MailAttempt.STATUS_SUCCESS
        response = f"sent={result}"
        logger.info(f"Письмо успешно отправлено: {recipient_email}")
    except Exception as exc:
        status = MailAttempt.STATUS_FAIL
        response = str(exc)
        logger.error(f"Ошибка при отправке письма на {recipient_email}: {exc}")
    return status, response


def send_mailing_instance(mailing, from_email):
    """Отправляет письма всем получателям выбранной рассылки."""
    logger.info(f"Запуск рассылки #{mailing.pk}: {mailing.message.subject}")
    mailing.status = Mailing.STATUS_RUNNING
    mailing.save(update_fields=["status"])

    for recipient in mailing.recipients.all():
        status, response = send_email_to_recipient(
            mailing.message.subject, mailing.message.body, recipient.email, from_email
        )
        MailAttempt.objects.create(mailing=mailing, recipient=recipient, status=status, server_response=response)

    mailing.status = Mailing.STATUS_FINISHED if timezone.now() >= mailing.end_at else Mailing.STATUS_RUNNING
    mailing.save(update_fields=["status"])
    logger.info(f"Рассылка #{mailing.pk} завершена со статусом {mailing.status}.")
