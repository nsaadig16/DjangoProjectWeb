from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout as auth_logout, login
from django.shortcuts import redirect

from WebProjecte.services.profile_image import generate_avatar
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
from .forms import UserCardForm
from .models import Card, CollectionCard, Collection
from .models import CardSet
import os
import uuid
import requests
from django.core.files.base import ContentFile
# Create your views here.

def home(request):
    return render(request, 'home.html')


class ProfileUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    dicebear_url = forms.CharField(widget=forms.HiddenInput(), required=False)

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
            
            # Verificar si se subió una nueva imagen de perfil o se usó DiceBear
            has_new_upload = request.FILES.get('profile_image') is not None
            dicebear_url = form.cleaned_data.get('dicebear_url')
            
            # Manejar actualización de imagen de perfil
            if has_new_upload or dicebear_url:
                # Eliminar imagen anterior si existe y no es la predeterminada
                if profile.profile_image:
                    try:
                        image_path = profile.profile_image.path
                        if os.path.exists(image_path) and 'default.jpg' not in image_path:
                            os.remove(image_path)
                    except Exception as e:
                        messages.error(request, f"Error al eliminar la imagen anterior: {e}")
                
                # Nombre consistente para todas las imágenes de perfil
                profile_filename = f"profilepic_{user.username}.png"
                
                # Guardar nueva imagen basada en la fuente
                if dicebear_url:
                    # Usar DiceBear tiene prioridad sobre la subida manual
                    try:
                        response = requests.get(dicebear_url)
                        if response.status_code == 200:
                            # Usar siempre el mismo formato de nombre para todas las imágenes
                            profile_filename = f"profilepic_{user.username}.png"
                            profile.profile_image.save(
                                profile_filename,
                                ContentFile(response.content),
                                save=False
                            )
                    except Exception as e:
                        messages.error(request, f"Error al descargar la imagen de perfil: {e}")
                elif has_new_upload:
                    # Procesar imagen subida manualmente - usar exactamente el mismo nombre
                    # para mantener consistencia y evitar tener múltiples archivos
                    uploaded_image = request.FILES['profile_image']
                    profile_filename = f"profilepic_{user.username}.png"
                    profile.profile_image.save(
                        profile_filename,
                        uploaded_image,
                        save=False
                    )
                
                # Limpiar el campo del formulario para evitar guardar dos veces
                form.cleaned_data['profile_image'] = None

            user.save()
            profile = form.save()
            
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            
            # Si se cambió la contraseña, volver a iniciar sesión
            if password:
                return redirect('login')
                
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    context = {
        'profile': profile,
        'form': form,
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

def api_cartas(request):
    cartas = Card.objects.select_related('rarity')
    data = [{
        'nombre': carta.title,
        'imagen': carta.image.url,
        'texto': carta.description,
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
        form = UserCardForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            return redirect('home')
    else:
        form = UserCardForm()

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
def open_pack_view(request, set_id):
    card_set = get_object_or_404(CardSet, pk=set_id)

    if request.method == 'POST':
        cards = open_pack(request.user, card_set.id)
        return render(request, 'pack_opened.html', {'cards': cards})

    return render(request, 'open_pack.html', {'card_set': card_set})

@login_required
def pack_selector_view(request):
    card_sets = CardSet.objects.all()
    return render(request, 'select_pack.html', {'card_sets': card_sets})


@login_required
def refresh_avatar(request):
    if request.method == 'POST':
        success = generate_avatar(request.user)
        if success:
            messages.success(request, 'Avatar correctly updated.')
        else:
            messages.error(request, 'Error updating avatar.')
        return redirect('profile')
    return render(request, 'profile.html')

def coleccion_view(request):
    collection = Collection.objects.get(user=request.user)


    cartas_usuario_ids = set(
        CollectionCard.objects.filter(collection=collection).values_list('card_id', flat=True)
    )

    cartas = []
    for carta in Card.objects.all().order_by('id'):
        cartas.append({
            'id': carta.id,
            'nombre': carta.title,
            'image': carta.image,
            'tiene': carta.id in cartas_usuario_ids
        })

    return render(request, 'coleccion.html', {'cartas': cartas})