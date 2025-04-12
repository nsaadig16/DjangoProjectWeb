from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout as auth_logout, login
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from .models import Card

from django.contrib.auth.decorators import user_passes_test
from .forms import CardForm
# Create your views here.

def home(request):
    return render(request, 'home.html')


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Profile
        fields = ['profile_image']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return self.instance.user.username

        # Verificar si el nombre de usuario ya existe y no es el usuario actual
        if User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso')

        return username


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user = request.user

            # Actualizar nombre de usuario si ha cambiado
            username = form.cleaned_data.get('username')
            if username and username != user.username:
                user.username = username

            # Actualizar contraseña si se proporcionó una nueva
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)

            user.save()
            form.save()

            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('profile')

    context = {
        'profile': profile,
    }
    return render(request, 'profile.html', context)


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

def card(request):
    return render(request,'card.html')

def cards(request):
    cartas = Card.objects.all().select_related('rarity', 'card_set')
    return render(request, 'cards.html', {'cartas': cartas})

def api_cartas(request):
    cartas = Card.objects.select_related('rarity')
    data = [{
        'nombre': carta.title,
        'imagen': carta.image_url,
        'texto': carta.description,
        'poder': getattr(carta, 'poder', '?'),
        'coste': getattr(carta, 'coste', 0),
        'tipo': carta.rarity.title
    } for carta in cartas]
    return JsonResponse(data, safe=False)

# Asegúrate de que solo los administradores puedan acceder
def is_admin(user):
    return user.is_staff


@user_passes_test(is_admin)
def add_card(request):
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cards')  # redirigir a la lista de cartas o donde prefieras
    else:
        form = CardForm()

    return render(request, 'add_card.html', {'form': form})
