from django.shortcuts import render, redirect,  get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Form, Question, Choice, FormResponse, QuestionResponse
from users.models import CustomUser
from courses.models import Course, Team
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Avg


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
    

def student_landing(request):
    if request.user.is_authenticated:
       username = request.user.username

       try:
           social_account = request.user.socialaccount_set.filter(provider='google').first()
           if social_account:
               username = social_account.extra_data.get('name', username)
       except:
           pass
    else:
       username = "Guest"
    context = {
        'username': username,
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

@login_required
def create_form_view(request):
    if request.method == 'POST':
        # Get the deadline value, only set it if it's not empty
        deadline = request.POST.get('deadline')
        if not deadline:
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
        
        return redirect('main:manage_forms')
    
    # Get all courses and teams for the template
    courses = Course.objects.filter(creator=request.user)  # Only show professor's courses
    teams = Team.objects.filter(course__in=courses) # Only show teams for the selected course (How?)
    
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
