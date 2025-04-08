from django.shortcuts import render, redirect,  get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from .models import Form, Question, Choice, FormResponse, QuestionResponse
from courses.models import Course, Team
from django.core.paginator import Paginator


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
    # Get all forms for courses where the user is enrolled as a student
    student_forms = Form.objects.filter(course__students__email=request.user.email).order_by('-created_at')
    return render(request, 'main/student_forms.html', {'forms': student_forms})

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
            creator=request.user
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
    teams = Team.objects.all()
    
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

    if request.method == 'POST':
        # Create the form response
        form_response = FormResponse.objects.create(
            form=form,
            student=request.user
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
                    question_response.selected_choice_id = answer
                elif question.question_type == 'rating':
                    question_response.rating_value = int(answer)
                
                question_response.save()
        
        return redirect('main:student_forms')
    return render(request, 'main/fill_form.html', {'form': form, 'questions': questions})

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
