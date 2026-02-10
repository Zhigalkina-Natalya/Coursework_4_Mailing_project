from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Mailing, Message, Recipient


class RecipientForm(forms.ModelForm):
    """Форма для создания и редактирования получателя."""

    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]


class MessageForm(forms.ModelForm):
    """Форма для создания и редактирования сообщения."""

    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(forms.ModelForm):
    """Форма для создания и редактирования рассылки."""

    class Meta:
        model = Mailing
        fields = ["start_at", "end_at", "status", "message", "recipients"]

    def clean(self):
        """Проверяет, что дата окончания позже даты начала."""
        cleaned_data = super().clean()
        start_at = cleaned_data.get("start_at")
        end_at = cleaned_data.get("end_at")

        if start_at and end_at and end_at <= start_at:
            raise ValidationError("Дата окончания рассылки должна быть позже даты начала.")
        if start_at and start_at < timezone.now():
            raise ValidationError("Дата начала не может быть в прошлом.")
        return cleaned_data
