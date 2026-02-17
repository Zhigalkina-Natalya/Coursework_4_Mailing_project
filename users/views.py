from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import FormView, View

from users.forms import LoginForm, RegisterForm, ResendActivationForm
from users.models import User


class RegisterView(FormView):
    """Регистрация нового пользователя с отправкой письма активации."""

    template_name = "users/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        """Создаёт неактивного пользователя и отправляет письмо активации."""
        user = form.save()
        self.send_activation_email(user)
        messages.success(self.request, "Регистрация успешна. Проверьте почту для активации.")
        return super().form_valid(form)

    def send_activation_email(self, user):
        """Формирует и отправляет письмо активации."""
        current_site = get_current_site(self.request)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activate_url = self.request.build_absolute_uri(
            reverse_lazy("users:activate", kwargs={"uidb64": uid, "token": token})
        )
        message = render_to_string(
            "users/activation_email.html",
            {"user": user, "activate_url": activate_url, "domain": current_site.domain},
        )
        send_mail(
            "Активация аккаунта",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class ActivateUserView(View):
    """Подтверждает аккаунт пользователя по ссылке из письма."""

    def get(self, request, uidb64, token):
        """Проверяет токен и активирует пользователя."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()
                login(request, user)
                messages.success(request, "Аккаунт успешно активирован!")
            else:
                messages.info(request, "Аккаунт уже был активирован ранее.")
            return redirect("users:login")

        return render(request, "users/activation_invalid.html")


class ResendActivationView(FormView):
    """Повторная отправка письма активации по email."""

    template_name = "users/resend_activation.html"
    success_url = reverse_lazy("users:login")
    form_class = ResendActivationForm

    def form_valid(self, form):
        """Повторно отправляет письмо активации, если пользователь существует и неактивен."""
        email = form.cleaned_data.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.info(self.request, "Аккаунт уже активирован.")
            else:
                RegisterView.send_activation_email(self, user)
                messages.success(self.request, "Письмо активации повторно отправлено.")
        except User.DoesNotExist:
            messages.error(self.request, "Пользователь с таким email не найден.")
        return super().form_valid(form)


class LoginView(DjangoLoginView):
    """Аутентификация пользователя."""

    template_name = "users/login.html"
    authentication_form = LoginForm


class LogoutView(View):
    """Выход пользователя из системы."""

    def get(self, request):
        """Выполняет выход пользователя из системы и перенаправляет на страницу входа."""
        logout(request)
        messages.info(request, "Вы вышли из системы.")
        return redirect("users:login")


@login_required
@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="Менеджеры").exists())
def user_list(request):
    """Просмотр всех пользователей (для менеджеров и админов)."""
    users = User.objects.all()
    return render(request, "users/user_list.html", {"users": users})


@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name="Менеджеры").exists())
def toggle_user_active(request, pk):
    """Менеджер может заблокировать или разблокировать пользователя."""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, "Нельзя изменить статус суперпользователя.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

    state = "активирован" if user.is_active else "заблокирован"
    messages.info(request, f"Пользователь «{user.email}» {state}.")

    return redirect("users:user_list")
