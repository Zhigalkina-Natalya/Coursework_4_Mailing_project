from django.contrib import admin

from .models import MailAttempt, Mailing, Message, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "start_at", "end_at", "status")
    filter_horizontal = ("recipients",)


@admin.register(MailAttempt)
class MailAttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "attempted_at", "status")
