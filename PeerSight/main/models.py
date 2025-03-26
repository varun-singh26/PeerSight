from django.db import models
from django.conf import settings

class Form(models.Model):
    title = models.CharField(max_length=200)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    FORM_TYPES = [
        ('likert', 'Likert'),
        ('mcq', 'Multiple Choice'),
    ]
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    question_type = models.CharField(max_length=10, choices=FORM_TYPES)

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
