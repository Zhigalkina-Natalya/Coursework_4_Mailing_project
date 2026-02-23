from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройки отображения пользователей в админке."""

    list_display = ("email", "phone", "country", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "country")
    search_fields = ("email", "phone", "country")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        ("Основные данные", {"fields": ("email", "password")}),
        ("Персональная информация", {"fields": ("avatar", "phone", "country")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Системные данные", {"fields": ("last_login", "date_joined")}),
    )

    exclude = ("username",)
