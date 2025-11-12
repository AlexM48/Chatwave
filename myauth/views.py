
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()
        password2 = request.POST.get("password2").strip()

        if password != password2:
            messages.error(request, "Пароли не совпадают")
            return render(request, "myauth/register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Пользователь с таким именем уже существует")
            return render(request, "myauth/register.html")

        user = User.objects.create_user(username=username, password=password)
        messages.success(request, "Регистрация прошла успешно")
        login(request, user)
        return redirect("mychat:room_list")

    return render(request, "myauth/register.html")

