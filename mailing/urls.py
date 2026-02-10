from django.urls import path

from . import views

app_name = "mailing"

urlpatterns = [
    path("", views.index, name="index"),  # главная
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list"),
    path("recipients/add/", views.RecipientCreateView.as_view(), name="recipient_add"),
    path("recipients/<int:pk>/edit/", views.RecipientUpdateView.as_view(), name="recipient_edit"),
    path("recipients/<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_delete"),
    # messages
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/add/", views.MessageCreateView.as_view(), name="message_add"),
    # mailings
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/add/", views.MailingCreateView.as_view(), name="mailing_add"),
    path("mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/send/", views.send_mailing_view, name="mailing_send"),  # ручной запуск через UI
]
