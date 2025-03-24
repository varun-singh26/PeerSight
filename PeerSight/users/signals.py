# Explicitly makes sure users default to "student" upon account creation though Google:
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

# Wait for a user to be created, then set their role to "student" if it isn't already set.
@receiver(post_save, sender=CustomUser)
def set_default_role(sender, instance, created, **kwargs):
    if created and not instance.role:
        instance.role = 'student'
        instance.save()

# If a superuser promotoes a user to professor, they'll get is_staff=True the next time they log in.
# is_staff allows access to Django Admin. 
@receiver(user_logged_in)
def assign_staff_status_based_on_role(request, user, **kwargs):
    if user.role == 'professor' and not user.is_staff:
        user.is_staff = True
        user.save()
    elif user.role != 'professor' and user.is_staff:
        user.is_staff = False
        user.save()
