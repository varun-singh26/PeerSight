from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('professor', 'Professor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def is_professor(self):
        return self.role == 'professor'

    def is_student(self):
        return self.role == 'student'
