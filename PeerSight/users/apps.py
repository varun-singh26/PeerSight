from django.apps import AppConfig


# What does this class do?
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

   #This ensures that Google-auth'd users get "student" if role isn't set.
    def ready(self):
        import users.signals # Ensures signals are registered
