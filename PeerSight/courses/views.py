from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Team
from main.decorators import professor_required
from django.db import IntegrityError
from django.db.models import Q
from users.models import CustomUser # use your actual import path

from django.contrib.auth import get_user_model

User = get_user_model()

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

        # Look for an existing user with this email or student ID
        student = CustomUser.objects.filter(
            Q(student_id=student_id) | Q(email=email),
            role='student'
        ).first()

        if student:
            # Update missing fields if possible
            updated = False

            if not student.student_id and student_id:
                student.student_id = student_id
                updated = True
            
            if not student.email and email:
                student.email = email
                updated = True
            
            if updated:
                student.save()

        else:
            try:
                # Prevent duplicate usernames from being created
                base_usernmame = email.split('@')[0]
                username = base_usernmame
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_usernmame}{counter}"
                    counter += 1
                
                student = CustomUser.objects.create_user(
                    username=username, # auto-generate username
                    email=email,
                    role='student',
                    name=name,
                    student_id=student_id,
                    graduation_year=graduation_year,
                )
                student.set_unusable_password()  # Set password to unusable (users sign in w/ Google Auth, no password needed for our platform)
                student.save()
            except IntegrityError:
                student = CustomUser.objects.filter(
                    Q(student_id=student_id) | Q(email=email),
                    role='student'
                ).first()

            
        # Add to course
        student.courses.add(course)

        # Add to team
        if new_team_name:
            team = Team.objects.create(course=course, name=new_team_name)
            team.members.add(student)
        elif team_id:
            team = Team.objects.get(id=team_id)
            team.members.add(student)

        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, "courses/add_student.html", {
        'course': course,
        'teams': teams
    })

'''
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

       try:
            user = User.objects.get(email=email)
       except User.DoesNotExist:
           user = User.objects.create_user(username=email.split('@')[0], email=email, password=User.objects.make_random_password())

       student = Student.objects.filter(Q(student_id=student_id) | Q(email=email)).first()

       if student:
           # Optional: Ensure it's the right student
           if student.student_id != student_id or student.email != email:
               # handle mismatch (log, warn, or abort)
               # Inform the professor that they entered either a student_id or email of a student that already exists in the db
               # But the other half (student_id or email) does not match the student that already exists in the db
               pass
       else:
           # Create a new student w/ the specified id and email 
           try:
               student = Student.objects.create(
                   user=user,
                   name=name,
                   student_id=student_id,
                   email=email,
                   graduation_year=graduation_year,
               )
            # If an IntegrityError occurs, it means that a student with the same email or student_id already exists
            # Then fetch that student
           except IntegrityError:
               # Race condition fallback
               student = Student.objects.get(Q(student_id=student_id) | Q(email=email)).first()
       
       student.courses.add(course) #Works in both directions
       print(f"Added {student.name} to course {course.name}")
       print("Current students in course:", course.students.all())       
       
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
'''

@professor_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)
    students = course.students.all().prefetch_related('teams')

    # Create a mapping: student.id -> their team (for this this course only)
    student_team_map = {}
    for student in students:
        team = student.teams.filter(course=course).first()
        student_team_map[student.id] = team # This will be none if no teams exists for this student in this course
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'students': students,
        'student_team_map': student_team_map
    })

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


@professor_required
def manage_teams_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)
    teams = course.teams.prefetch_related('members')
    students = course.students.all()

    # Identify students not in any team in this course
    assigned_student_ids = set()
    for team in teams:
        assigned_student_ids.update(member.id for member in team.members.all())
    unassigned_students = students.exclude(id__in=assigned_student_ids)

    return render(request, 'courses/manage_teams.html', {
        'course': course,
        'teams': teams,
        "unassigned_students": unassigned_students
    })

@professor_required
def create_team_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)

    if request.method == 'POST':
        team_name = request.POST['name']
        Team.objects.create(course=course, name=team_name)
        return redirect('courses:manage_teams', course_id=course.id)
    
    return render(request, 'courses/create_team.html', {'course': course})


@professor_required
def add_member_view(request, course_id, team_id):
    course = get_object_or_404(Course, id=course_id, creator=request.user)
    team = get_object_or_404(Team, id=team_id, course=course)

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        if not student_id:
            # Handle the error
            #messages.error(request, "Student ID is missing.")
            return redirect('courses:manage_teams', course_id=course_id)
        
        # Grab the student (CustomUser) by ID and confirm they're a student
        student = get_object_or_404(CustomUser, id=student_id, role='student')

        # Enforce one-team-per-course rule
        already_on_team = course.teams.filter(members=student).exists()
        if already_on_team:
            # Optionally flash a warning message here
            #messages.error(request, "Student is already on a team in this course.")
            return redirect('courses:manage_teams', course_id=course.id)
        
        # Add student to this team             
        team.members.add(student)
        return redirect('courses:manage_teams', course_id=course.id)
    

    



