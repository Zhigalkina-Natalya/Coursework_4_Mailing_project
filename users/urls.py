from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    # Основной функционал пользователей
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("activate/<uidb64>/<token>/", views.ActivateUserView.as_view(), name="activate"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("resend-activation/", views.ResendActivationView.as_view(), name="resend_activation"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile_edit"),
    # Раздел менеджера: управление пользователями
    path("", views.user_list, name="user_list"),
    path("<int:pk>/toggle/", views.toggle_user_active, name="toggle_user_active"),
]
