from django.urls import path
from .views import RegistrarUsuarioView, LoginUsuarioView, SessionStatusView, LogoutUsuarioView

urlpatterns = [
    path('register/', RegistrarUsuarioView.as_view()),
    path('login/', LoginUsuarioView.as_view()),
    path('session-status/', SessionStatusView.as_view()),
    path('logout/', LogoutUsuarioView.as_view()),
]
