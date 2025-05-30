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
from .models import Card, CollectionCard, Collection ,CardSet , UserCard
import os
import requests
from django.core.files.base import ContentFile
from .models import PackStatus
from django.utils import timezone

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

        # Check if the username already exists and is not the current user
        if User.objects.filter(username=username).exclude(id=self.instance.user.id).exists():
            raise forms.ValidationError('This username is already in use')

        return username


@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Manage account deletion
        if action == 'delete_account':
            user = request.user

            try:
                # Delete the profile image if it exists and is not the default one
                if hasattr(user, 'profile') and user.profile.profile_image:
                    try:
                        image_path = user.profile.profile_image.path
                        if os.path.exists(image_path) and 'default.jpg' not in image_path:
                            os.remove(image_path)
                    except Exception as e:
                        print(f"Error when deleting profile image: {e}")

                # Delete friend requests related to the user
                FriendRequest.objects.filter(Q(from_user=user) | Q(to_user=user)).delete()

                # Delete collection and its cards if they exist
                try:
                    collection = Collection.objects.get(user=user)
                    CollectionCard.objects.filter(collection=collection).delete()
                    collection.delete()
                except Collection.DoesNotExist:
                    pass

                # Close session and log out the user
                auth_logout(request)

                # Delete the user account and profile
                user.delete()

                messages.success(request, 'Your account has been successfully deleted.')
                return redirect('home')

            except Exception as e:
                messages.error(request, f'Error on account deletion: {e}')
                return redirect('profile')

        # Handle normal profile update
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user = request.user

            # Update username if it has changed
            username = form.cleaned_data.get('username')
            if username and username != user.username:
                user.username = username

            # Update password if a new one was provided
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            # Check if a new profile image was uploaded or DiceBear was used
            has_new_upload = request.FILES.get('profile_image') is not None
            dicebear_url = form.cleaned_data.get('dicebear_url')
            
            # Handle profile image update
            if has_new_upload or dicebear_url:
                # Delete previous image if it exists and is not the default one
                if profile.profile_image:
                    try:
                        image_path = profile.profile_image.path
                        if os.path.exists(image_path) and 'default.jpg' not in image_path:
                            os.remove(image_path)
                    except Exception as e:
                        messages.error(request, f"Error deleting previous image: {e}")
                
                # Consistent name for all profile images
                profile_filename = f"profilepic_{user.username}.png"
                
                # Save new image based on source
                if dicebear_url:
                    # Using DiceBear takes priority over manual upload
                    try:
                        response = requests.get(dicebear_url)
                        if response.status_code == 200:
                            # Always use the same name format for all images
                            profile_filename = f"profilepic_{user.username}.png"
                            profile.profile_image.save(
                                profile_filename,
                                ContentFile(response.content),
                                save=False
                            )
                    except Exception as e:
                        messages.error(request, f"Error downloading profile image: {e}")
                elif has_new_upload:
                    # Process manually uploaded image - use exactly the same name
                    # for consistency and to avoid having multiple files
                    uploaded_image = request.FILES['profile_image']
                    profile_filename = f"profilepic_{user.username}.png"
                    profile.profile_image.save(
                        profile_filename,
                        uploaded_image,
                        save=False
                    )
                
                # Clear form field to avoid saving twice
                form.cleaned_data['profile_image'] = None

            user.save()
            profile = form.save()
            
            messages.success(request, 'Your profile has been successfully updated.')
            
            # If password was changed, log in again
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
            login(request, user)  # Authenticate the user after registration
            return redirect("home")  # Redirect to the main page
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


def how_to_play(request):
    return render(request, 'how_to_play.html')

def api_cards(request):
    cards = Card.objects.select_related('rarity')
    data = [{
        'name': card.title,
        'image': card.image.url,
        'text': card.description,
        'power': getattr(card, 'power', '?'),
        'cost': getattr(card, 'cost', 0),
        'type': card.rarity.title
    } for card in cards]
    return JsonResponse(data, safe=False)
@login_required
def user_cards_api(request):
    user = request.user
    user_cards = CollectionCard.objects.filter(collection__user=user)

    data = [
        {
            'name': cc.card.title,
            'text': cc.card.description,
            'image': cc.card.image.url,
            'type': cc.card.card_set.title,
            'rarity': cc.card.rarity.title if hasattr(cc.card, 'rarity') else '',
        }
        for cc in user_cards
    ]

    return JsonResponse(data, safe=False)

@login_required
def add_card(request):
    if request.method == 'POST':
        form = UserCardForm(request.POST, request.FILES)
        if form.is_valid():
            previous_cards = UserCard.objects.filter(user=request.user)
            for card in previous_cards:
                if card.image:
                    card.image.delete(save=False)
            previous_cards.delete()

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
    status, _ = PackStatus.objects.get_or_create(user=request.user)
    status.update_packs()

    if request.method == 'POST':
        if status.packs_available > 0:
            status.packs_available -= 1
            status.last_opened = timezone.now()
            status.save()

            collection = Collection.objects.get(user=request.user)
            owned_card_ids = set(CollectionCard.objects.filter(collection=collection).values_list('card_id', flat=True))

            cards = open_pack(request.user, card_set.id)

            cards_with_status = []
            for card in cards:
                is_new = card.id not in owned_card_ids
                cards_with_status.append({'card': card, 'is_new': is_new})

            return render(request, 'pack_opened.html', {
                'cards_with_status': cards_with_status
            })
        else:
            messages.error(request, 'You have no packs available. Please wait for regeneration.')
            return redirect('open_pack', set_id=set_id)

    return render(request, 'open_pack.html', {
        'card_set': card_set,
        'packs_available': status.packs_available
    })

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

def collection_view(request):
    user_cards_ids = set()

    if request.user.is_authenticated:
        try:
            collection = Collection.objects.get(user=request.user)
            user_cards_ids = set(
                CollectionCard.objects.filter(collection=collection).values_list('card_id', flat=True)
            )
        except Collection.DoesNotExist:
            # If the user does not have a collection, we can skip this part
            pass

    cards = []
    for card in Card.objects.all().order_by('id'):
        cards.append({
            'id': card.id,
            'name': card.title,
            'image': card.image,
            'has': card.id in user_cards_ids
        })

    return render(request, 'collection.html', {'cards': cards})