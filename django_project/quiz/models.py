from django.db import models

class Card(models.Model):
    user_name = models.CharField(max_length=100)
    cards = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    hashtag = models.TextField(max_length=100, null=True)
    likes = models.IntegerField(default=0, null=True)
    downloads = models.IntegerField(default=0, null=True)
    number_of_quiz = models.IntegerField(default=0, null=True)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    question = models.TextField(max_length=200, null=True)
    answer = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.answer

class Login(models.Model):
    user_name = models.CharField(max_length=100, null=True)
    time = models.DateTimeField(auto_now_add=True, null=True)

class Search_time(models.Model):
    keyword =models.TextField(max_length=200, default=None, null=True)
    time = models.DateTimeField(auto_now_add=True, null=True)

class Download_time(models.Model):
    card_title = models.TextField(max_length=200, default=None, null=True)
    time = models.DateTimeField(auto_now_add=True, null=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)

class Make_time(models.Model):
    card_title = models.TextField(max_length=200, default=None, null=True)
    time = models.DateTimeField(auto_now_add=True, null=True)

class Preference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user) + ':' + str(self.card)

