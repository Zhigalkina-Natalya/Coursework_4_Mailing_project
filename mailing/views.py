from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import MailingForm, MessageForm, RecipientForm
from .models import MailAttempt, Mailing, Message, Recipient
from .services import send_mailing_instance


class OwnerFilterMixin(LoginRequiredMixin):
    """Гибкий миксин: фильтрует только если модель имеет поле owner."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # менеджеры и суперпользователи видят всё
        if user.is_superuser or user.groups.filter(name="Менеджеры").exists():
            return qs

        # если модель имеет поле 'owner' — фильтруем по нему
        model = self.model
        if hasattr(model, "owner"):
            return qs.filter(owner=user)

        # если у модели нет поля 'owner', но есть связь с mailing -> фильтруем по владельцу рассылки
        if hasattr(model, "_meta") and "mailing" in [f.name for f in model._meta.get_fields()]:
            return qs.filter(mailing__owner=user)

        # иначе ничего не фильтруем (безопасно)
        return qs


class OwnerCreateMixin(LoginRequiredMixin):
    """Автоматически проставляет владельца при создании."""

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerPermissionMixin(LoginRequiredMixin):
    """Запрещает редактировать или удалять чужие объекты."""

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if (
            obj.owner != request.user
            and not request.user.is_superuser
            and not request.user.groups.filter(name="Менеджеры").exists()
        ):
            messages.error(request, "У вас нет прав для этого действия.")
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CacheClearMixin:
    """Очищает кеш после успешного сохранения формы."""

    def form_valid(self, form):
        response = super().form_valid(form)
        cache.clear()
        return response


class ContextTitleMixin:
    """Автоматически добавляет заголовок и ссылку 'Отмена' в контекст."""

    title = None
    cancel_url = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title or self.model._meta.verbose_name.capitalize()
        context["cancel_url"] = self.cancel_url or self.success_url
        return context


@login_required(login_url="/users/login/")
def index(request):
    """Главная страница со статистикой рассылок."""
    user = request.user

    if user.is_superuser or user.groups.filter(name="Менеджеры").exists():
        total = Mailing.objects.count()
        active = Mailing.objects.filter(status=Mailing.STATUS_RUNNING).count()
        recipients = Recipient.objects.count()
    else:
        total = Mailing.objects.filter(owner=user).count()
        active = Mailing.objects.filter(owner=user, status=Mailing.STATUS_RUNNING).count()
        recipients = Recipient.objects.filter(owner=user).count()

    context = {
        "total_mailings": total,
        "active_mailings": active,
        "unique_recipients": recipients,
    }
    return render(request, "mailing/index.html", context)


# CRUD для получателей
class RecipientListView(OwnerFilterMixin, ListView):
    """Список получателей (только свои, если не менеджер)."""

    model = Recipient
    template_name = "mailing/recipient_list.html"


class RecipientCreateView(ContextTitleMixin, CacheClearMixin, OwnerCreateMixin, CreateView):
    """Создание получателя."""

    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:recipient_list")
    title = "Добавить получателя"


class RecipientUpdateView(ContextTitleMixin, OwnerPermissionMixin, UpdateView):
    """Редактирование получателя (только владельцем или суперпользователем)."""

    model = Recipient
    form_class = RecipientForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:recipient_list")
    title = "Редактировать получателя"


class RecipientDeleteView(ContextTitleMixin, OwnerPermissionMixin, DeleteView):
    """Удаление получателя."""

    model = Recipient
    template_name = "mailing/_confirm_delete.html"
    success_url = reverse_lazy("mailing:recipient_list")
    title = "Удалить получателя"


# CRUD для сообщений
@method_decorator(cache_page(60 * 5), name="dispatch")
class MessageListView(OwnerFilterMixin, ListView):
    """Список сообщений с кешированием и фильтром по владельцу."""

    model = Message
    template_name = "mailing/message_list.html"


class MessageCreateView(ContextTitleMixin, CacheClearMixin, OwnerCreateMixin, CreateView):
    """Создание сообщения с владельцем и очисткой кеша"""

    model = Message
    form_class = MessageForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:message_list")
    title = "Добавить сообщение"


class MessageUpdateView(ContextTitleMixin, OwnerPermissionMixin, CacheClearMixin, UpdateView):
    """Редактирование сообщения."""

    model = Message
    form_class = MessageForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:message_list")
    title = "Редактировать сообщение"


class MessageDeleteView(ContextTitleMixin, OwnerPermissionMixin, CacheClearMixin, DeleteView):
    """Удаление сообщения."""

    model = Message
    template_name = "mailing/_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")
    title = "Удалить сообщение"


# CRUD для рассылок
@method_decorator(cache_page(60 * 5), name="dispatch")
class MailingListView(OwnerFilterMixin, ListView):
    """Список рассылок с кешированием и фильтром по владельцу."""

    model = Mailing
    template_name = "mailing/mailing_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["is_manager_or_admin"] = user.is_superuser or user.groups.filter(name="Менеджеры").exists()
        return context


class MailingCreateView(ContextTitleMixin, CacheClearMixin, OwnerCreateMixin, CreateView):
    """Создание рассылки с подсказками формата даты"""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:mailing_list")
    title = "Создать рассылку"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDetailView(OwnerPermissionMixin, DetailView):
    """Просмотр деталей рассылки."""

    model = Mailing
    template_name = "mailing/mailing_detail.html"
    title = "Просмотр рассылки"

    def get_object(self, queryset=None):
        """Пересчёт и обновление статуса при открытии страницы рассылки."""
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingUpdateView(ContextTitleMixin, OwnerPermissionMixin, CacheClearMixin, UpdateView):
    """Редактирование рассылки."""

    model = Mailing
    form_class = MailingForm
    template_name = "mailing/_form_base.html"
    success_url = reverse_lazy("mailing:mailing_list")
    title = "Редактировать рассылку"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MailingDeleteView(ContextTitleMixin, OwnerPermissionMixin, CacheClearMixin, DeleteView):
    """Удаление рассылки."""

    model = Mailing
    template_name = "mailing/_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")
    title = "Удалить рассылку"


def send_mailing_view(request, pk):
    """Ручная отправка рассылки из интерфейса (только владелец/менеджер/админ)."""

    mailing = get_object_or_404(Mailing, pk=pk)

    user = request.user
    if not (user == mailing.owner or user.is_superuser or user.groups.filter(name="Менеджеры").exists()):
        messages.error(request, "У вас нет прав на отправку этой рассылки.")
        raise PermissionDenied

    if request.method == "POST":
        send_mailing_instance(mailing, settings.DEFAULT_FROM_EMAIL)
        messages.success(request, f"Рассылка «{mailing.message.subject}» отправлена.")
    return redirect("mailing:mailing_detail", pk=pk)


@permission_required("mailing.can_disable_mailings", raise_exception=True)
def toggle_mailing_activity(request, pk):
    """Пользователь с правом 'can_disable_mailings' может включать/отключать рассылку."""
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.is_active = not mailing.is_active
    mailing.save(update_fields=["is_active"])

    cache.clear()

    state = "включена" if mailing.is_active else "отключена"
    messages.info(request, f"Рассылка «{mailing.message.subject}» {state}.")
    return redirect("mailing:mailing_list")


class MailAttemptListView(OwnerFilterMixin, ListView):
    """Список попыток рассылок (только свои, если не менеджер/админ)."""

    model = MailAttempt
    template_name = "mailing/mailattempt_list.html"
    context_object_name = "attempts"

    def get_queryset(self):
        qs = super(ListView, self).get_queryset().select_related("mailing", "recipient")
        user = self.request.user
        if user.is_superuser or user.groups.filter(name="Менеджеры").exists():
            return qs.order_by("-attempted_at")
        return qs.filter(mailing__owner=user).order_by("-attempted_at")
