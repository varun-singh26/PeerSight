from django.db import models
from django.conf import settings
from courses.models import Team

class Form(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True)
    teams = models.ManyToManyField(Team, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Text'),
        ('mcq', 'Multiple Choice'),
        ('likert', 'Likert'),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.form.title} - {self.question_text}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.question.question_text} - {self.choice_text}"
