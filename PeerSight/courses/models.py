from django.db import models
from django.conf import settings


# Create your models here.

class Course(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'professor'},
        on_delete=models.CASCADE,
        related_name='courses_created',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    semester = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    course_id = models.CharField(max_length=50)
    enrollment_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.course_id})"
    
class Team(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name = 'teams')
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams', limit_choices_to={"role": "student"}, blank=True)

    def __str__(self):
        return f"{self.name} ({self.course.name})"
