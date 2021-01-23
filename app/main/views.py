from . import main
from flask import render_template, redirect, url_for, session, request, flash
from .forms import QuestionForm, CoursesForm
from flask_login import login_required, current_user
from ..decorators import requires_teacher
from ..models import Course, Question, Result, User
from .. import db
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import IntegrityError

def create_question_object(form, question_id=None):
    """
    Function to be called in create_question
    and edit question routes

    return: returns a question instance
    """
    if question_id:
        question = Question.query.get_or_404(question_id)
    else:
        question = Question()
        #if the question is a new question, assign it a user, which will be the
        #user id of the current user that will definitely be a teacher
        question.user=current_user._get_current_object()
    #The following lines of codes populate the field of the question instance
    #with the data submitted by the field and returns it
    question.body = form.body.data
    question.a = form.a.data
    question.b = form.b.data
    question.c = form.c.data if form.b.data else None
    question.d = form.d.data if form.b.data else None
    question.e = form.e.data if form.b.data else None
    question.correct = form.correct.data if form[form.correct.data].data else None
    question.course_id = form.course_id.data
    question.is_structural = False if form.b.data else True

    return question

def get_score(form):
    """
    This function handles the calculation of the score of submitted quiz
    questions

    return: the score
    """
    score = 0

    for question_id, my_answer in form.items():
        question = Question.query.get_or_404(question_id)
        if (not question.is_structural) and (question.correct == my_answer):
            #if the question is not a structural question and the andwer is correct
            score += 1
        elif (question.is_structural) and (question.a.lower() == my_answer.lower()):
            #if the question is a structural question and is correct
            score += 1
    return score

def save_score(score, course, teacher):
    if current_user.is_authenticated: #if the current user is logged in
        result_query = Result.query.filter_by(user_id=current_user.id).filter_by(course_id=course).filter_by(teacher_id=teacher).first()
        if result_query is None:
            result = Result()
            result.course_id=course
            result.user=current_user
            result.teacher_id=teacher
            result.highest_score=score
            db.session.add(result)
            db.session.commit()
            return True
        elif score > result_query.highest_score:
            result_query.highest_score = score
            db.session.add(result_query)
            db.session.commit()
            return True
    return False

@main.route('/', methods=['GET'])
def index():
    """
    The function that handles the homepage

    return: returns the index html template
    """
    return render_template('index.html')

@main.route('/courses', methods=['GET', 'POST'])#route for all courses created
def courses():
    """
    This function handles the creation and display of list of available courses

    return: should return a template of list of courses and also a form if for
    the user to enter a new course name if they are a teacher
    """
    courses = Course.query.order_by('course_name').all()
    if current_user.is_teacher:
        form = CoursesForm()
        if form.validate_on_submit():
            course_exists = Course.query.filter_by(course_name=form.course_name.data.lower()).first()
            if course_exists:
                flash(f'A Course named {form.course_name.data} already exists')
                return redirect(url_for('main.courses'))
            new_course = Course(course_name=form.course_name.data.lower())
            db.session.add(new_course)
            db.session.commit()
            flash(f'A Course named {form.course_name.data} has been created by you')
            return redirect(url_for('main.courses'))
        return render_template('courses.html', form=form, courses=courses)
    return render_template('courses.html', courses=courses)

@main.route('/delete-course/<int:id>', methods=['GET'])
@login_required
@requires_teacher
def delete_course(id):
    """
    This function handles the deletion of courses  whose ids are passed, it is
    decorated by the requires_teacher decorator, i.e the user who visited the
    route that called this function is required to be a teacher

    return: should redirect to the courses route if the deletion was successful
    """
    course = Course.query.get_or_404(id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted')
        return redirect(url_for('main.courses'))

@main.route('/course/<int:id>', methods=['GET'])
def course(id):
    """
    This function handles the display of the details of the course that its
    id was passed to the function

    return: should return a template of the course with its details
    """
    quizes = Question.query.filter_by(course_id=id)
    if quizes.first() is None:
        flash('There are no questions for this course yet')
        return redirect(url_for('main.index'))
    course = quizes.first().course
    teachers = {quiz.user for quiz in quizes}
    return render_template('course.html', teachers=teachers, course=course)

@main.route('/create-question', methods=['GET', 'POST'])
@login_required
@requires_teacher
def create_question():
    """
    This function handles the creation of questions

    return: should return a template containing the question form, it is
    decorated by the requires_teacher decorator, i.e the user who visited the
    route that called this function is required to be a teacher
    """
    #sets the default course in the course select field
    form = QuestionForm(course_id=session.get('selected_course'))
    if form.validate_on_submit():
        if not session.get('selected_course') or not form.course_id.data == session.get('selected_course'):
            session['selected_course'] = form.course_id.data

        question_object = create_question_object(form)
        try:
            db.session.add(question_object)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('An error occured, please check your input and ensure that\
             the option you picked as the correct option exists')
            return render_template('create_or_edit_question.html', form=form)
        flash(f'A multiple choice question has been created by you') if form.b.data else \
        flash(f'A structural question has been created by you')
        return redirect(url_for('main.create_question'))
    return render_template('create_or_edit_question.html', form=form)

@main.route('/edit-question/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_teacher
def edit_question(id):
    """
    This function handles the editing of questions whose ids are passed into
    the function, decorated by the requires_teacher decorator, also ensures
    that the person trying to edit a question is the creator

    return: should return a template containing the question form, the form
    fields should be filled
    """
    if not current_user.owns_question(id):
        flash('The question you tried to edit was not created by you')
        return redirect(url_for('main.index'))
    form = QuestionForm()

    if form.validate_on_submit():
        question_object = create_question_object(form, id)
        try:
            db.session.add(question_object)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('An error occured, please check your input and ensure that\
             the option you picked as the correct option exists')
            return redirect(url_for('main.edit_question', id=id))
        flash('Question edited and is now a multiple choice question') if form.b.data else\
        flash('Question edited and is now a structural question')
        return redirect(url_for('main.my_questions'))

    """
        there is a reason this part is below and not above
        the reason is that, putting it at the top keeps
        changing the edited values to the initial values
        that they were before editing
    """
    question = Question.query.get_or_404(id)
    form.body.data = question.body
    form.a.data = question.a
    form.b.data = question.b
    form.c.data = question.c
    form.d.data = question.d
    form.e.data = question.e
    form.correct.data = question.correct
    form.course_id.data = question.course_id

    return render_template('create_or_edit_question.html', form=form)

@main.route('/delete/<int:id>')
@login_required
@requires_teacher
def delete_question(id):
    """
    This function handles the deletion of questions whose ids were passed,
    decorated by the requires_teacher decorator, also it ensures that the
    person trying to delete the question was the creator

    return: should return a template
    """
    if not current_user.owns_question(id):
        flash('The question you tried to delete was not created by you')
        return redirect(url_for('main.index'))
    question = Question.query.get_or_404(id)
    if question:
        db.session.delete(question)
        db.session.commit()
        flash('Question deleted')
        return redirect(url_for('main.my_questions'))

@main.route('/my-questions', methods=['GET'])
@login_required
@requires_teacher
def my_questions():
    """
    This function handles the display of the currently logged in teacher

    return: should return a template containing the questions created by
    the currently logged in teacher
    """
    my_questions = Question.query.filter_by(user=current_user._get_current_object())
    return render_template('my_questions.html', my_questions=my_questions)

@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    """
    This function handles the quiz

    return: should return a template containing the questions to be answered by the user
    as well as the result of the just taken test
    """
    course = request.args.get('course')
    teacher = request.args.get('teacher')
    quizes = Question.query.filter_by(course_id=course).filter_by(user_id=teacher).order_by(func.random()).limit(10)
    tname = quizes.first().user.username #teacher name
    cname = quizes.first().course.course_name #course name
    if request.method == 'POST':
        score = get_score(request.form)
        score_saved = save_score(score, course, teacher)
        if score_saved:
            flash(f'Your highest score in this quiz is {score} which is also your score in the test')
        else:
           flash(f'Your score in this quiz is {score} ')
        return redirect(url_for('main.quiz', course=course, teacher=teacher))
    return render_template('quiz.html', quizes=quizes, cname=cname, tname=tname)

@main.route('/my-results', methods=['GET'])
@login_required
def my_results():
    """
    This function handles the display of the results of the currently
    logged in user, decorated by the login_required decorator

    return: should return a template containing all the highest scored
    to the quizes taken by the currently logged in user
    """
    my_results = Result.query.filter_by(user=current_user._get_current_object()).all()
    for my_result in my_results:
        my_result.teacher_name = User.query.get_or_404(my_result.teacher_id).username
    return render_template('my_results.html', my_results=my_results)
