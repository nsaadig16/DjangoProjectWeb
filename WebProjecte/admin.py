from django.contrib import admin
from django.contrib.auth.models import User

from .models import Card, Rarity, CardSet, Profile, Collection, CollectionCard, UserCard

admin.site.register(Card)
admin.site.register(Rarity)
admin.site.register(CardSet)
admin.site.register(Profile)
admin.site.register(Collection)
admin.site.register(CollectionCard)
admin.site.register(UserCard)