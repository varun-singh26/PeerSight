from django.shortcuts import render, redirect,  get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from .models import Form, Question, Choice
from courses.models import Course, Team

# Create your views here.

# After user signs, in checks role and redirects accordingly
@login_required
def route_user(request):
    user = request.user
    if user.role == "professor":
        return redirect("admin_landing")
    else:
        return redirect("student_landing")

def admin_landing(request):
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

    return render(request, 'main/admin.html', context)

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
def create_form_view(request):
    if request.method == 'POST':
        # Get the deadline value, only set it if it's not empty
        deadline = request.POST.get('deadline')
        if not deadline:
            deadline = None

        form_instance = Form.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            deadline=deadline,
            course_id=request.POST.get('course'),
            creator=request.user
        )
        
        # Save selected teams
        selected_teams = request.POST.getlist('teams')
        form_instance.teams.set(selected_teams)
        
        # Save questions and their choices
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
                
                if question_type == 'mcq':
                    choices_text = request.POST.get(f'choices_{question_number}')
                    if choices_text:
                        for choice_text in choices_text.split('\n'):
                            if choice_text.strip():
                                Choice.objects.create(
                                    question=question,
                                    choice_text=choice_text.strip()
                                )
        
        return redirect('manage_forms')
    
    # Get all courses and teams for the template
    courses = Course.objects.all()
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
        responses = []
        for question in questions:
            answer = request.POST.get(f'question_{question.id}')
            if answer is not None:
                responses.append((question.question_text, answer))
        return redirect('thank_you_page') 
    return render(request, 'main/fill_form.html', {'form': form, 'questions': questions})

def thank_you_page(request):
    return render(request, 'main/thank_you.html')
