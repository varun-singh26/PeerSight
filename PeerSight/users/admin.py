from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Makes role visible and editable in the admin interface (/admin)
    list_display = ('username', 'email', 'name', 'role', 'student_id', 'graduation_year', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('name', 'student_id', 'graduation_year', 'courses')}),
        ('Permissions', {'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'name', 'student_id', 'graduation_year', 'courses', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email', 'student_id')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
