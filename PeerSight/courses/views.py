from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Student, Team
from main.decorators import professor_required

# Create your views here.

@professor_required
def add_student_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)
    
    teams = course.teams.all()

    if request.method == 'POST':
       name = request.POST['name']
       student_id = request.POST['student_id']
       graduation_year = request.POST['graduation_year']
       email = request.POST['email']
       team_id = request.POST.get('team', None)
       new_team_name = request.POST.get('new_team_name', None) 

       student, created = Student.objects.get_or_create(
           student_id=student_id,
           defaults={'name': name, 'graduation_year': graduation_year, 'email': email}
       )
       student.courses.add(course)
       
       if new_team_name:
            team = Team.objects.create(course=course, name=new_team_name)
            team.members.add(student)  # Add student to the new team
       elif team_id:
            team = Team.objects.get(id=team_id)
            team.members.add(student)
            
       student.courses.add(course)
       
       return redirect('courses:course_detail', course_id=course.id)
    
    teams = course.teams.all()
    
    return render(request, "courses/add_student.html", {
        'course': course,
        'teams': teams
    })

@professor_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)
    students = course.students.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'students': students
    })
    
def create_course_view(request):
    if request.method == 'POST':
        Course.objects.create(
            creator=request.user,
            name=request.POST['name'],
            subject=request.POST['subject'],
            semester=request.POST['semester'],
            section=request.POST['section'],
            course_id=request.POST['course_id']
        )
    return redirect('courses:manage_courses')

def manage_courses_view(request):
    courses = Course.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'courses/manage_courses.html', {'courses': courses})



