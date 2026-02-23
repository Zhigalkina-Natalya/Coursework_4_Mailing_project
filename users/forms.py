from django import forms
from django.contrib.auth.forms import AuthenticationForm

from users.models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email",)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Пароли не совпадают")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # Активируем через email
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


class ResendActivationForm(forms.Form):
    """Форма для повторной отправки письма активации."""

    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Введите email"})
    )


class ProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя."""

    class Meta:
        model = User
        fields = ("avatar", "phone", "country")
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7..."}),
            "country": forms.TextInput(attrs={"class": "form-control", "placeholder": "Страна"}),
        }
