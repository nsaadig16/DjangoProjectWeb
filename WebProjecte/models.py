import os

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from WebProjecte.services.profile_image import generate_avatar
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Collection(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Collection of {self.user.username}"


class Rarity(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    probability = models.FloatField()

    def __str__(self):
        return self.title


class CardSet(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='card_sets', blank=True, null=True)

    def __str__(self):
        return self.title


class Card(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='card_images', blank=True, null=True)
    rarity = models.ForeignKey(Rarity, on_delete=models.CASCADE)
    card_set = models.ForeignKey(CardSet, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return None


class CollectionCard(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    class Meta:
        unique_together = ('card', 'collection')

    def __str__(self):
        return f"{self.quantity} x {self.card.title} in {self.collection}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    friends = models.ManyToManyField("self", symmetrical=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')


@receiver(post_save, sender=User)
def create_user_profile_and_collection(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Collection.objects.create(user=instance)
        generate_avatar(instance)  # Avatar generation via API


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
