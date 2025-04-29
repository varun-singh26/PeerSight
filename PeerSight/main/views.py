from django.shortcuts import render, redirect,  get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Form, Question, Choice, FormResponse, QuestionResponse, Grade
from users.models import CustomUser
from courses.models import Course, Team
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Avg
from main.tasks import send_form_created_email, send_form_deadline_reminder
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta



# Create your views here.

# After user signs, in checks role and redirects accordingly
@login_required
def route_user(request):
    user = request.user
    if user.role == "professor":
        return redirect("main:admin_landing")
    else:
        return redirect("main:student_landing")

def admin_landing(request):
    if request.user.is_authenticated:
        username = request.user.username

        try:
            social_account = request.user.socialaccount_set.filter(provider='google').first()
            if social_account:
                username = social_account.extra_data.get('name', username)
        except:
            pass

        user_courses = Course.objects.filter(creator=request.user)
        
        user_forms = Form.objects.filter(creator=request.user).order_by('-created_at')  
        
        paginator = Paginator(user_forms, 3)  
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'username': username,
            'user_courses': user_courses,
            'page_obj': page_obj,
        }
        
        return render(request, 'main/admin.html', context)
    else:
        return render(request, 'main/admin.html', {'username': 'Guest'})
    
@login_required
def student_landing(request):
    user = request.user
    username = user.first_name or user.username

    user_teams = Team.objects.filter(members=user).prefetch_related('forms')

    assigned_forms = set()
    for team in user_teams:
        for form in team.forms.all():
            assigned_forms.add((form, team))

    assigned_tasks = []
    now = timezone.now()
    for form, team in assigned_forms:
        is_completed = FormResponse.objects.filter(form=form, student=user).exists()

        assigned_tasks.append({
            'name': form.title,
            'due_date': form.deadline.strftime("%A %I:%M%p") if form.deadline else "No deadline",
            'status': 'completed' if is_completed else 'pending',
            'tag': form.course.name if form.course else "General",
            'form_id': form.id,
        })

    user_classes = Course.objects.filter(students=user).select_related('creator')

    teams = Team.objects.filter(members=user).prefetch_related('members')

    team_data = []
    for team in teams:
        team_forms = team.forms.all()
        todo_form = team_forms.exclude(responses__student=user).first()

        team_data.append({
            'name': team.name,
            'members': [member.get_full_name() or member.username for member in team.members.all()],
            'to_do': todo_form.title if todo_form else None,
        })

    context = {
        'username': username,
        'assigned_tasks': assigned_tasks,
        'user_classes': user_classes,
        'teams': team_data,
    }

    return render(request, 'main/landing_user.html', context)

def signin(request):
    return render(request, "users/signin.html", {}) 
    


def user_logout(request):
    logout(request) #logout the user
    return redirect("/") #return to signin page

FormForm = modelform_factory(Form, fields=['title'])
QuestionFormSet = modelformset_factory(Question, fields=('question_text', 'question_type'), extra=3)

@login_required
def student_forms_view(request):
    student = request.user

    #Get all the teams the student is on
    teams = student.teams.select_related('course').prefetch_related('forms')

    # Build a mapping from form to the team it's assigned to (from this student's teams)
    form_team_map = {}
    student_forms = set()

    for team in teams:
        for form in team.forms.all():
            student_forms.add(form)
            form_team_map[form.id] = team # This works assuming each form is assigned to only one team per student
    
    #Convert to list and sort
    student_forms = sorted(list(student_forms), key=lambda f: f.created_at, reverse=True) #

    return render(request, 'main/student_forms.html', {
        'forms': student_forms,
        'form_team_map': form_team_map,
    })

    # Get all forms for courses where the user is enrolled as a student
    student_forms = Form.objects.filter(course__students__email=request.user.email).order_by('-created_at')
    return render(request, 'main/student_forms.html', {'forms': student_forms})

@login_required
def get_teams_for_course(request, course_id):
    teams = Team.objects.filter(course_id=course_id).values('id', 'name')
    return JsonResponse(list(teams), safe=False)

from django.utils.dateparse import parse_datetime

@login_required
def create_form_view(request):
    if request.method == 'POST':
        deadline_raw = request.POST.get('deadline')
        if deadline_raw:
            deadline = parse_datetime(deadline_raw)
        else:
            deadline = None

        # Get the selected course
        course_id = request.POST.get('course')
        course = Course.objects.get(id=course_id)

        form_instance = Form.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            deadline=deadline,
            course=course,
            creator=request.user,
            allow_multiple_responses=request.POST.get('allow_multiple_responses') == 'on' 
        )
        
        # Save selected teams
        selected_teams = request.POST.getlist('teams')
        form_instance.teams.set(selected_teams)
        
        # Save questions
        for key, value in request.POST.items():
            if key.startswith('question_text_'):
                question_number = key.split('_')[2]
                question_type = request.POST.get(f'question_type_{question_number}')
                
                # Convert checkbox value to boolean
                required = request.POST.get(f'required_{question_number}') == 'on'
                
                question = Question.objects.create(
                    form=form_instance,
                    question_text=value,
                    question_type=question_type,
                    required=required,
                    order=int(question_number)
                )

                # Handle multiple choice options
                if question_type == 'multiple_choice':
                    choices_text = request.POST.get(f'choices_{question_number}')
                    if choices_text:
                        choices = [choice.strip() for choice in choices_text.split('\n') if choice.strip()]
                        for choice_text in choices:
                            Choice.objects.create(
                                question=question,
                                choice_text=choice_text
                            )

        ## 🔥 --- ADD THIS RIGHT AFTER EVERYTHING IS SAVED ---
        # Get all students in the course
        students = CustomUser.objects.filter(teams__course=course).distinct()
        student_emails = [student.email for student in students]

        # Send immediate notification
        if student_emails:
            send_form_created_email.delay(course.name, form_instance.title, student_emails)

            # Schedule reminder if deadline exists
            if form_instance.deadline:
                send_time = form_instance.deadline - timedelta(days=1)
                send_form_deadline_reminder.apply_async(
                    args=[form_instance.title, student_emails],
                    eta=send_time
                )
        ## 🔥 --- END OF ADDED PART ---

        return redirect('main:manage_forms')
    
    # Get all courses and teams for the template
    courses = Course.objects.filter(creator=request.user)  # Only show professor's courses
    teams = Team.objects.filter(course__in=courses) # Only show teams for the selected course

    return render(request, 'main/create_form.html', {
        'courses': courses,
        'teams': teams
    })


def manage_forms_view(request):
    forms = Form.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'main/manage_forms.html', {'forms': forms})

def form_detail_view(request, form_id):
    form = get_object_or_404(Form, id=form_id, creator=request.user)
    questions = form.questions.all()  
    return render(request, 'main/form_detail.html', {
        'form': form,
        'questions': questions
    })

def fill_form_view(request, form_id):
    form = get_object_or_404(Form, id=form_id)
    questions = form.questions.all()

    # Get the student's team for this course
    student = request.user
    teams = student.teams.filter(course=form.course)

    # Assume only one team per course (enforce this elsewhere)
    team = teams.first()
    teammates = team.members.exclude(id=student.id) if team else []

    if form.allow_multiple_responses:
        target_student_id = request.POST.get('target_student') if request.method == 'POST' else None
        target_student = CustomUser.objects.filter(id=target_student_id).first() if target_student_id else None



        if request.method == 'POST':
            # Validation: ensure target is on the same team
            if not target_student or target_student not in teammates:
                messages.error(request, "Invalid teammate selected.")
                return redirect('main:fill_form', form_id=form.id)
            
            # Prevent duplicate submissions
            existing = FormResponse.objects.filter(form=form, student=student, target_student=target_student).first()
            if existing:
                messages.warning(request, f"You've already submitted a response for {target_student.get_full_name()}.")
                return redirect('main:student_forms')

            # Create the form response
            form_response = FormResponse.objects.create(
                form=form,
                student=student,
                target_student=target_student
            )
            
            # Save each question response
            for question in questions:
                answer = request.POST.get(f'question_{question.id}')
                if answer is not None:
                    question_response = QuestionResponse(
                        form_response=form_response,
                        question=question
                    )
                    
                    if question.question_type == 'text':
                        question_response.answer_text = answer
                    elif question.question_type == 'multiple_choice':
                        try:
                            choice = Choice.objects.get(id=answer)
                            question_response.selected_choice = choice
                        except Choice.DoesNotExist:
                            # optionally log this or skip saving
                            pass
                    elif question.question_type == 'likert':
                        print(f"LIKERT DEBUG | question_{question.id} = {answer}")
                        question_response.rating_value = int(answer)
                    
                    question_response.save()
            
            return redirect('main:student_forms')
        
    else:
        # Single-response form mode
        if request.method == 'POST':
            existing = FormResponse.objects.filter(form=form, student=student).first()
            if existing:
                messages.warning(request, "You've already submitted this form.")
                return redirect('main:student_forms')
            
            form_response = FormResponse.objects.create(
                form=form,
                student=student
            )
            for question in questions:
                answer = request.POST.get(f'question_{question.id}')
                if answer is not None:
                    qr = QuestionResponse(form_response=form_response, question=question)
                    if question.question_type == 'text':
                        qr.answer_text = answer
                    elif question.question_type == 'multiple_choice':
                        try:
                            choice = question.choices.get(id=answer)
                            qr.selected_choice = choice
                        except:
                            pass
                    elif question.question_type == 'likert':
                        qr.rating_value = int(answer)
                    qr.save()

            return redirect('main:student_forms') 
    return render(request, 'main/fill_form.html', {
        'form': form, 
        'questions': questions, 
        'teammates': teammates,
        'allow_multiple_responses': form.allow_multiple_responses
    })

@login_required
def view_responses(request):
    # Only allow professors to view responses
    if request.user.role != 'professor':
        return redirect('main:student_landing')
    
    # Get all forms created by the professor
    forms = Form.objects.filter(creator=request.user).order_by('-created_at')
    
    # Get responses for each form
    form_responses = {}
    for form in forms:
        responses = form.responses.all().select_related('student')
        form_responses[form] = responses
    
    return render(request, 'main/view_responses.html', {
        'form_responses': form_responses
    })

def thank_you_page(request):
    return render(request, 'main/thank_you.html')



@require_POST
@login_required
def publish_grades(request):
    if not request.user.is_professor():
        return HttpResponseForbidden()
    
    form_id = request.POST.get('form_id')
    team_id = request.POST.get('team_id')

    team = get_object_or_404(Team, id=team_id)
    form = get_object_or_404(Form, id=form_id)

    
    # Publish grades for the form
    grades = Grade.objects.filter(
        form=form,
        student__in=team.members.all()
    )

    grades.update(published=True)

    return redirect(request.META.get("HTTP_REFERER", '/'))


@require_POST
@login_required
def assign_grade(request):
    if not request.user.is_professor():
        return HttpResponseForbidden()
    
    student_id = request.POST.get('student_id')
    form_id = request.POST.get('form_id')
    grade_value = request.POST.get('grade_value')

    Grade.objects.update_or_create(
        student_id=student_id,
        form_id=form_id,
        defaults={
            'professor': request.user,
            'grade_value': grade_value,
            'published': False,
        }
    )

    return redirect(request.META.get("HTTP_REFERER", '/'))

@login_required
def evaluate_student_responses(request):
    if not request.user.is_professor():
        return redirect('main:student_landing')
    
    courses = Course.objects.filter(creator=request.user)
    selected_course_id = request.GET.get('course')
    selected_form_id = request.GET.get('form')
    selected_team_id = request.GET.get('team')

    forms = Form.objects.none()
    teams = Team.objects.none()
    evaluations = []

    can_publish = False

    if selected_course_id:
        forms = Form.objects.filter(course__id=selected_course_id, creator=request.user)

        if selected_form_id:
            form = get_object_or_404(Form, id=selected_form_id)
            teams = form.teams.filter(course_id=selected_course_id)

            if selected_team_id:
                team = get_object_or_404(Team, id=selected_team_id)
                questions = Question.objects.filter(form=form)
                question_map = {q.id: q.question_text for q in questions}

            
                for student in team.members.all():
                    # Get all FormResponses submitted *about* this student
                    responses_about_student = FormResponse.objects.filter(
                        form=form,
                        target_student=student
                    )

                    # fetch student's grade (may or may not exist), we'll deal w/ this when passing to template
                    grade = Grade.objects.filter(
                        student=student,
                        form=form
                    ).first()

                    if not responses_about_student.exists():
                        continue # skip students with no responses

                    likert_responses = QuestionResponse.objects.filter(
                        form_response__in=responses_about_student,
                        question__question_type='likert'
                    ).values('question').annotate(avg_score=Avg('rating_value'))

                    # Replace question IDs with text
                    likert_scores = [
                        {'question_text': question_map[entry['question']], 'avg_score': entry['avg_score']}
                        for entry in likert_responses
                    ]

                    comments = QuestionResponse.objects.filter(
                        form_response__in=responses_about_student,
                        question__question_type='text'
                    ).exclude(answer_text="").values_list('answer_text', flat=True)

                    evaluations.append({
                        'student': student,
                        'response_count': responses_about_student.count(),
                        'likert_scores': likert_scores,
                        'comments': comments,
                        'grade_value': grade.grade_value if grade else '', 
                    })

                # After building evaluations, check if all students have a grade
                if team.members.exists():
                    graded_students_count = Grade.objects.filter(
                        form_id=selected_form_id,
                        student__in=team.members.all(),
                    ).count()
                    if graded_students_count == team.members.count():
                        can_publish = True
                    
    return render(request, 'main/evaluate_responses.html', {
        'courses': courses,
        'forms': forms,
        'teams': teams,
        'selected_course_id': selected_course_id,
        'selected_form_id': selected_form_id,
        'selected_team_id': selected_team_id,
        'evaluations': evaluations,
        'can_publish': can_publish,
    })

@login_required
def student_responses(request):
    # Only allow professors to view responses
    if request.user.role != 'professor':
        return redirect('main:student_landing')
    
    # Get all responses for forms created by the professor, ordered by submission date
    responses = FormResponse.objects.filter(
        form__creator=request.user
    ).select_related('form', 'student').order_by('-submitted_at')
    
    return render(request, 'main/student_responses.html', {
        'responses': responses
    })

User = get_user_model()

@login_required
def student_response_details(request, response_id):
    # Only allow professors to view responses
    if request.user.role != 'professor':
        return redirect('main:student_landing')
    
    # Get the response and its details
    response = get_object_or_404(
        FormResponse.objects.select_related('form', 'student'),
        id=response_id,
        form__creator=request.user
    )
    
    # Get all question responses for this form submission
    question_responses = response.question_responses.all().select_related('question')
    
    return render(request, 'main/student_response_details.html', {
        'response': response,
        'question_responses': question_responses
    })

@login_required
def student_feedback_view(request, form_id, student_id):

    form = get_object_or_404(Form, id=form_id)
    student = get_object_or_404(User, id=student_id)

    # Average scores for likert/rating questions
    questions = form.questions.filter(question_type='likert')
    average_scores = []

    total_score = 0
    count = 0

    for question in questions:
        avg = QuestionResponse.objects.filter(
            question=question,
            form_response__form=form,
            form_response__student=student,
            rating_value__isnull=False
        ).aggregate(Avg('rating_value'))['rating_value__avg']

        if avg is not None:
            average_scores.append({
                'question': question.question_text,
                'average': avg
            })
            total_score += avg
            count += 1

    cumulative_score = total_score / count if count > 0 else 0

    comments_qs = QuestionResponse.objects.filter(
        question__form=form,
        form_response__student=student,
        question__question_type='text'
    ).exclude(answer_text="")

    comments = [c.answer_text for c in comments_qs]

    return render(request, 'main/student_feedback.html', {
        'student': student,
        'form': form,
        'average_scores': average_scores,
        'comments': comments,
        'cumulative_score': cumulative_score,
    })
