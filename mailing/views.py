from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .models import Mailing, Message, Recipient
from .services import send_mailing_instance


def index(request):
    """Главная страница со статистикой рассылок."""
    total = Mailing.objects.count()
    active = Mailing.objects.filter(status=Mailing.STATUS_RUNNING).count()
    recipients = Recipient.objects.count()
    context = {"total_mailings": total, "active_mailings": active, "unique_recipients": recipients}
    return render(request, "mailing/index.html", context)


# CRUD для получателей
class RecipientListView(ListView):
    """Список получателей."""

    model = Recipient
    template_name = "mailing/recipient_list.html"


class RecipientCreateView(CreateView):
    """Создание получателя."""

    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")


class RecipientUpdateView(UpdateView):
    """Редактирование получателя."""

    model = Recipient
    fields = ["email", "full_name", "comment"]
    template_name = "mailing/recipient_form.html"
    success_url = reverse_lazy("mailing:recipient_list")


class RecipientDeleteView(DeleteView):
    """Удаление получателя."""

    model = Recipient
    template_name = "mailing/recipient_confirm_delete.html"
    success_url = reverse_lazy("mailing:recipient_list")


# CRUD для сообщений
class MessageListView(ListView):
    """Список сообщений."""

    model = Message
    template_name = "mailing/message_list.html"


class MessageCreateView(CreateView):
    """Создание сообщения."""

    model = Message
    fields = ["subject", "body"]
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


# CRUD для рассылок
class MailingListView(ListView):
    """Список рассылок."""

    model = Mailing
    template_name = "mailing/mailing_list.html"


class MailingCreateView(CreateView):
    """Создание рассылки."""

    model = Mailing
    fields = ["start_at", "end_at", "status", "message", "recipients"]
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDetailView(DetailView):
    """Просмотр деталей рассылки."""

    model = Mailing
    template_name = "mailing/mailing_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


def send_mailing_view(request, pk):
    """Ручная отправка рассылки из интерфейса."""
    mailing = get_object_or_404(Mailing, pk=pk)
    if request.method == "POST":
        send_mailing_instance(mailing, settings.DEFAULT_FROM_EMAIL)
        messages.success(request, "Рассылка отправлена.")
    return redirect("mailing:mailing_detail", pk=pk)
