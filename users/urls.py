from django.urls import path
from users.views.auth_views import LoginPageView, LogoutPageView
from users.views.user_views import (
    UserListView,
    UserCreateView,
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    UserResetProfileView,
    UserResetAllProfilesView,
    SettingsView,
    CategoryResetView,
    ProfileListView,
)


urlpatterns = [
    # URLs d'authentification (déjà définies dans config/urls.py, mais on peut les mettre ici si on veut les regrouper)
    # path("login/", LoginPageView.as_view(), name="login"),
    # path("logout/", LogoutPageView.as_view(), name="logout"),

    # URLs de gestion des utilisateurs
    path("list/", UserListView.as_view(), name="users"),
    path("create/", UserCreateView.as_view(), name="user_create"),
    path("<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("<int:pk>/update/", UserUpdateView.as_view(), name="user_update"),
    path("<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    path("<int:pk>/reset-profile/", UserResetProfileView.as_view(), name="user_reset_profile"),

    # URLs de la page Réglages (superutilisateurs uniquement)
    path("settings/", SettingsView.as_view(), name="settings"),
    path("settings/reset-profiles/", UserResetAllProfilesView.as_view(), name="user_reset_all_profiles"),
    path("settings/reset-categories/", CategoryResetView.as_view(), name="category_reset"),
    path("profiles/", ProfileListView.as_view(), name="profiles"),
]