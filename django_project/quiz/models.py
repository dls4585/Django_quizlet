from django.db import models
from django.contrib.auth.models import User

class Card(models.Model):
    cards = models.ForeignKey('self', on_delete=models.CASCADE, default=None)
    title = models.CharField(max_length=100)
    description = models.TextField()
    likes = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    number_of_quiz = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    text = models.TextField(max_length=200)
    answer = models.CharField(max_length=100)

    def __str__(self):
        return self.answer

class Preference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ':' + str(self.card)