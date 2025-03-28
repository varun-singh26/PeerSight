from django.shortcuts import render, redirect,  get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory, modelformset_factory, inlineformset_factory
from django.contrib.auth.decorators import login_required
from .models import Form, Question, Choice


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

from django.shortcuts import render
from django import forms

FormForm = modelform_factory(Form, fields=['title'])

QuestionFormSet = modelformset_factory(Question, fields=('text', 'question_type'), extra=3)

def create_form_view(request):
    if request.method == 'POST':
        form_form = FormForm(request.POST)
        question_formset = QuestionFormSet(request.POST, queryset=Question.objects.none())

        if form_form.is_valid() and question_formset.is_valid():
            form_instance = form_form.save(commit=False)
            form_instance.creator = request.user
            form_instance.save()

            for question_form in question_formset:
                question = question_form.save(commit=False)
                question.form = form_instance
                question.save()

                if question.question_type == 'mcq':
                    choices_key = f'choices_{question_form.prefix}'
                    choices = request.POST.getlist(choices_key)
                    for choice_text in choices:
                        if choice_text.strip():
                            Choice.objects.create(question=question, text=choice_text.strip())

            return redirect('admin_landing')  

    else:
        form_form = FormForm()
        question_formset = QuestionFormSet(queryset=Question.objects.none())

    return render(request, 'main/create_form.html', {
    'form_form': form_form,
    'question_formset': question_formset,
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
                responses.append((question.text, answer))
        return redirect('thank_you_page') 
    return render(request, 'main/fill_form.html', {'form': form, 'questions': questions})


def thank_you_page(request):
    return render(request, 'main/thank_you.html')

def course_modification(request):
    return render(request, 'main/course_modification.html')
