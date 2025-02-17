from django.shortcuts import render
from django.contrib.auth import logout as auth_logout, login
from django.shortcuts import redirect
from .forms import CustomUserCreationForm



# Create your views here.

def home(request):
    return render(request, 'home.html')


def logout_view(request):
    auth_logout(request)
    return redirect('home')


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Autenticar al usuario después del registro
            return redirect("home")  # Redirigir a la página principal
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})