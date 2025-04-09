
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.email

class Collection(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"Collection of {self.user.name}"

class Rarity(models.Model):
    title=models.CharField(max_length=100)
    description=models.TextField()
    probability=models.FloatField()
    def __str__(self):
        return self.title

class CardSet(models.Model):
    title=models.CharField(max_length=100)
    description=models.TextField()
    image_url = models.URLField()
    def __str__(self):
        return self.title

class Card(models.Model):
    title=models.CharField(max_length=100)
    description=models.TextField()
    image_url = models.URLField()
    rarity=models.ForeignKey(Rarity, on_delete=models.CASCADE)
    card_set=models.ForeignKey(CardSet, on_delete=models.CASCADE)
    def __str__(self):
        return self.title

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

    def __str__(self):
        return f'{self.user.username} Profile'


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
