from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout as auth_logout, login
from django.shortcuts import redirect
from .forms import CustomUserCreationForm
from django.db.models import Q
from .models import Profile, FriendRequest
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from .utils import open_pack
from django.contrib.auth.decorators import user_passes_test
from .forms import CardForm
from .models import Card, CollectionCard, Collection
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

def api_cartas(request):
    cartas = Card.objects.select_related('rarity')
    data = [{
        'nombre': carta.title,
        'imagen': carta.image.url,
        'texto': carta.description,
        'poder': getattr(carta, 'poder', '?'),
        'coste': getattr(carta, 'coste', 0),
        'tipo': carta.rarity.title
    } for carta in cartas]
    return JsonResponse(data, safe=False)
@login_required
def user_cards_api(request):
    user = request.user
    user_cards = CollectionCard.objects.filter(collection__user=user)

    data = [
        {
            'nombre': cc.card.title,
            'texto': cc.card.description,
            'imagen': cc.card.image.url,
            'tipo': cc.card.card_set.title,
            'rareza': cc.card.rarity.title if hasattr(cc.card, 'rarity') else '',
        }
        for cc in user_cards
    ]

    return JsonResponse(data, safe=False)

@login_required()
def add_card(request):
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cards')  # redirigir a la lista de cartas o donde prefieras
    else:
        form = CardForm()

    return render(request, 'add_card.html', {'form': form})

@login_required
def friends_list(request):
    profile = request.user.profile
    query = request.GET.get('q')
    search_results = []

    if query:
        search_results = User.objects.filter(
            Q(username__icontains=query)
        ).exclude(id=request.user.id)

    context = {
        'friends': profile.friends.all(),
        'search_results': search_results,
        'query': query,
    }
    return render(request, 'friends/friends_list.html', context)

@login_required
def remove_friend(request, user_id):
    old_friend = get_object_or_404(User, id=user_id)
    request.user.profile.friends.remove(old_friend.profile)
    return redirect('friends_list')

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    return redirect('friends_list')

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    from_profile = friend_request.from_user.profile
    to_profile = request.user.profile

    from_profile.friends.add(to_profile)
    friend_request.delete()
    return redirect('friends_list')

@login_required
def reject_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    return redirect('friends_list')

@login_required
def open_pack_view(request):
    if request.method == 'POST':
        cards = open_pack(request.user)
        return render(request, 'pack_opened.html', {'cards': cards})
    return render(request, 'open_pack.html')

def coleccion_view(request):
    if request.user.is_authenticated:
        try:
            collection = Collection.objects.get(user=request.user)
            collection_cards = CollectionCard.objects.filter(collection=collection).select_related('card')
            cartas = [cc.card for cc in collection_cards]
        except Collection.DoesNotExist:
            cartas = []
    else:
        cartas = Card.objects.all()

    return render(request, 'coleccion.html', {'cartas': cartas})