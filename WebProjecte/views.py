from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout as auth_logout, login
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from .models import Profile
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required


# Create your views here.

def home(request):
    return render(request, 'home.html')


@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        image = request.FILES.get("profile_image")

        # Actualizar usuario
        request.user.username = username
        request.user.set_password(password)
        request.user.save()

        # Actualizar perfil
        profile.password = make_password(password)  # Guardar con hash
        if image:
            profile.profile_image = image
        profile.save()

        return redirect("profile")

    return render(request, "profile.html", {"profile": profile})


@login_required
def my_view(request):
    return redirect('login')  # Redirect to /login/


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


def como_jugar(request):
    return render(request, 'como_jugar.html')
