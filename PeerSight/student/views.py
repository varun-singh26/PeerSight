from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from main.models import Form, Team, FormResponse, QuestionResponse
from collections import defaultdict
from django.db.models import Avg

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


@login_required
def student_received_feedback_view(request):
    student = request.user

    # All responses where this student was the target
    responses = (
        FormResponse.objects
        .filter(target_student=student)
        .select_related('form__course')
        .prefetch_related('question_responses__question')
    )

    # Group by (course, form)
    grouped_feedback = defaultdict(lambda: defaultdict(list))

    for response in responses:
        course = response.form.course
        form = response.form
        grouped_feedback[course][form].append(response)
    
    # For each (course, form) --> collect average scores and comments
    feedback_data = []

    for course, forms in grouped_feedback.items():
        course_entry = {
            'course': course,
            'forms': []
        }
        for form, form_responses in forms.items():
            # Get all related question responses for this form/student
            qr_queryset = QuestionResponse.objects.filter(
                form_response__in=form_responses
            ).select_related('question')

            # Aggregate Likert responses
            likert_questions = form.questions.filter(question_type='likert')
            likert_averages = []
            for question in likert_questions:
                avg = qr_queryset.filter(question=question).aggregate(Avg('rating_value'))['rating_value__avg']
                if avg is not None:
                    likert_averages.append({
                        'question': question.question_text,
                        'average': round(avg, 1)
                    })
            # Collect text answers (comments)
            comments = [
                qr.answer_text for qr in qr_queryset
                if qr.question.question_type == 'text' and qr.answer_text.strip()
            ]

            course_entry['forms'].append({
                'form': form,
                'likert_averages': likert_averages,
                'comments': comments
            })
        feedback_data.append(course_entry)

    return render(request, 'student/received_feedback.html', {
        'feedback_data': feedback_data
    })

User = get_user_model()

# This view is for admin?
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


@login_required
def student_responses_view(request):
    student = request.user

    # Get all responses from this student
    responses = (
        FormResponse.objects
        .filter(student=student)
        .select_related('form__course')
        .order_by('-submitted_at')
    )

    # Build a mapping: response -> student team (per course)
    response_team_map = {}
    for response in responses:
        course = response.form.course
        team = student.teams.filter(course=course).first()
        response_team_map[response.id] = team

    return render(request, 'student/yourResponses.html', {
        'responses': responses,
        'response_team_map': response_team_map,
    })


@login_required
def student_response_details_view(request, response_id):
    student = request.user
    response = get_object_or_404(FormResponse, id=response_id, student=student)

    question_responses = response.question_responses.all().select_related('question')

    return render(request, 'student/yourResponseDetails.html', {
        'response': response,
        'question_responses': question_responses
    })

#def student_response_details_view(request, response_id):
    #response = get_object_or_404(FormResponse, id=response_id)
    #return render(request, 'student/yourResponseDetails.html', {"response": response})

    #'''questions = response.form.questions.all()

    #question_responses = QuestionResponse.objects.filter(form_response=response)

    # Build a mapping of question ID to its response
    #question_response_map = {qr.question.id: qr for qr in question_responses}

    #return render(request, 'student/yourResponseDetails.html', {
        #'response': response,
        #'questions': questions,
        #'question_response_map': question_response_map,
    #})'''


   
