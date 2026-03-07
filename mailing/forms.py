from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Mailing, Message, Recipient


class BootstrapFormMixin:
    """Добавляет Bootstrap-оформление и подсказки для ввода."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():

            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})

            if name in ["start_time", "end_time"]:
                field.widget.attrs.update({"placeholder": "Формат: ГГГГ-ММ-ДД ЧЧ:ММ (например, 2026-02-15 10:00)"})


class RecipientForm(BootstrapFormMixin, forms.ModelForm):
    """Форма для создания и редактирования получателя."""

    class Meta:
        model = Recipient
        fields = ["email", "full_name", "comment"]


class MessageForm(BootstrapFormMixin, forms.ModelForm):
    """Форма для создания и редактирования сообщения."""

    class Meta:
        model = Message
        fields = ["subject", "body"]


class MailingForm(BootstrapFormMixin, forms.ModelForm):
    """Форма для создания и редактирования рассылки с проверкой дат и фильтрацией по владельцу."""

    start_time = forms.DateTimeField(
        label="Дата начала",
        input_formats=["%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    end_time = forms.DateTimeField(
        label="Дата окончания",
        input_formats=["%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Фильтруем доступные сообщения и получателей по владельцу
        if user and not (user.is_superuser or user.groups.filter(name="Менеджеры").exists()):
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Recipient.objects.filter(owner=user)
        else:
            # менеджеры и суперпользователи видят всё
            self.fields["message"].queryset = Message.objects.all()
            self.fields["recipients"].queryset = Recipient.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and end_time <= start_time:
            raise ValidationError("Дата окончания рассылки должна быть позже даты начала.")

        if start_time and start_time < timezone.now():
            raise ValidationError("Дата начала рассылки не может быть в прошлом.")

        return cleaned_data
