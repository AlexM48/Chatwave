from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import register

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name="myauth/login.html"), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
