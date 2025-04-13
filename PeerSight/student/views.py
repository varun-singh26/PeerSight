from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main.models import Form, Team
from collections import defaultdict

# Create your views here.

@login_required
def student_form_dashboard_view(request):
    student = request.user # CustomUser instance (role='student')
    courses = student.courses.all()
    course_team_map = {}
    forms_by_course = {}

    for course in courses:
        #Get the student's team(s) in this course (supports multiple if needed)
        teams = Team.objects.filter(course=course, members=student)
        course_team_map[course.id] = ', '.join(team.name for team in teams) if teams else "Unassigned"

        # Get all forms in this course assigned to the student's team(s)
        forms = Form.objects.filter(course=course, teams__in=teams).distinct()
        forms_by_course[course.id] = forms
    
    return render(request, 'student/form_dashboard.html', {
        'student': student,
        'courses': courses,
        'course_team_map': course_team_map,
        'forms_by_course': forms_by_course,
    })

   
