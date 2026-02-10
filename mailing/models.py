from django.utils import timezone

from django.db import models


class Recipient(models.Model):
    """Получатель рассылки: email, имя, комментарий."""

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.email} ({self.full_name})" if self.full_name else self.email


class Message(models.Model):
    """Сообщение рассылки: тема и тело письма."""

    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return f"Сообщение: {self.subject}"


class Mailing(models.Model):
    """Рассылка: период, статус, сообщение и получатели."""

    STATUS_CREATED = "CREATED"
    STATUS_RUNNING = "RUNNING"
    STATUS_FINISHED = "FINISHED"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="mailings")
    recipients = models.ManyToManyField(Recipient, related_name="mailings", blank=True)

    def __str__(self):
        return f"Рассылка №{self.pk} — {self.message.subject}"

    def compute_status(self):
        """Вычислить статус рассылки по времени."""
        now = timezone.now()
        if now < self.start_at:
            return self.STATUS_CREATED
        if self.start_at <= now <= self.end_at:
            return self.STATUS_RUNNING
        return self.STATUS_FINISHED

    def update_status(self):
        """Пересчитать и при необходимости сохранить статус в базе."""
        new_status = self.compute_status()
        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])


class MailAttempt(models.Model):
    """Попытка отправки письма по рассылке."""

    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAIL = "FAIL"
    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAIL, "Не успешно"),
    ]

    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts")
    recipient = models.ForeignKey(Recipient, null=True, blank=True, on_delete=models.SET_NULL, related_name='attempts')
    attempted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    server_response = models.TextField(blank=True)

    def __str__(self):
        return f"Попытка №{self.pk} для рассылки №{self.mailing.pk} - {self.get_status_display()}"
