from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_welcome_email(email, course_name):
    send_mail(
        subject="You've been added to a course!",
        message=f"Hello! You've been added to the course: {course_name}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


@shared_task
def send_form_created_email(course_name, form_title, emails):
    send_mail(
        subject=f"New Form Created in {course_name}!",
        message=f"A new form '{form_title}' has been created for your course!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=False,
    )

@shared_task
def send_form_deadline_reminder(form_title, emails):
    send_mail(
        subject=f"Reminder: Form '{form_title}' is Due Soon!",
        message=f"Just a reminder: the form '{form_title}' is due in less than 24 hours. Make sure to submit!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=False,
    )



