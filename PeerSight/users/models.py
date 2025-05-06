from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('professor', 'Professor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)
    courses = models.ManyToManyField('courses.Course', related_name='students', blank=True)


    def is_professor(self):
        return self.role == 'professor'

    def is_student(self):
        return self.role == 'student'
