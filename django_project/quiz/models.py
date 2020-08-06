from django.db import models

class Card(models.Model):
    user_name = models.CharField(max_length=100)
    cards = models.ForeignKey('self', on_delete=models.CASCADE, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    likes = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    number_of_quiz = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    question = models.TextField(max_length=200)
    answer = models.CharField(max_length=100)

    def __str__(self):
        return self.answer

class login(models.Model):
    user_name = models.CharField(max_length=100)
    time = models.DateTimeField(auto_now_add=True)

class search_time(models.Model):
    keyword =models.TextField(max_length=200, default=None)
    time = models.DateTimeField(auto_now_add=True)

class download_time(models.Model):
    card_title = models.TextField(max_length=200, default=None)
    time = models.DateTimeField(auto_now_add=True)

class make_time(models.Model):
    card_title = models.TextField(max_length=200, default=None)
    time = models.DateTimeField(auto_now_add=True)
