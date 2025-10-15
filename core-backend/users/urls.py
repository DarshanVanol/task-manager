from django.urls import path

from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/",views.ProfileView.as_view(), name="profile")
]