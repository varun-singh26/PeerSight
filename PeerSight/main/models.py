from django.db import models
from django.conf import settings
from courses.models import Course, Team

# Removing null = True and blank = True from the course field in Form model. Every form MUST BELONG to a course
class Form(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='forms', null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    teams = models.ManyToManyField(Team, related_name='forms', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    allow_multiple_responses = models.BooleanField(default=False, help_text="Allow each student to submit one response per teammate")

    def is_peer_evaluation(self):
        return self.allow_multiple_responses
    
    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('text', 'Short Answer'),
        ('multiple_choice', 'Multiple Choice'),
        ('likert', 'Likert'),
    ]
    
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.form.title} - {self.question_text}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)

    def __str__(self):
        return self.choice_text

class FormResponse(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submitted_responses") # the evaluator
    target_student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_responses", null=True, blank=True) # the evaluatee
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['form', 'student', 'target_student']

    def __str__(self):
        return f"{self.student.username}'s response to {self.form.title}"


class QuestionResponse(models.Model):
    form_response = models.ForeignKey(FormResponse, on_delete=models.CASCADE, related_name='question_responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    rating_value = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Response to {self.question.question_text}"
