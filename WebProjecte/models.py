from django.contrib.auth.models import AbstractUser
from django.db import models

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

