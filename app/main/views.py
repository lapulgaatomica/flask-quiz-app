from . import main
from flask import render_template, redirect, url_for, session, request, flash
from .forms import QuestionForm, CoursesForm
from flask_login import login_user, logout_user, login_required, current_user
from ..decorators import requires_teacher
from ..models import Course, Question
from .. import db

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/courses', methods=['GET', 'POST'])#route for all courses created
def courses():
    courses = Course.query.order_by('course_name').all()
    if current_user.is_teacher:
        form = CoursesForm()
        if form.validate_on_submit():
            search = Course.query.filter_by(course_name=form.course_name.data.lower()).first()
            if search:
                flash(f'A Course named {form.course_name.data} already exists')
                return redirect(url_for('main.courses'))
            course = Course(course_name=form.course_name.data.lower())
            db.session.add(course)
            db.session.commit()
            flash(f'A Course named {form.course_name.data} has been created')
            return redirect(url_for('main.courses'))
        return render_template('courses.html', form=form, courses=courses)
    return render_template('courses.html', courses=courses)

@main.route('/create-question', methods=['GET', 'POST'])
@login_required
@requires_teacher
def create_question():
    #sets the default course in the course select field
    form = QuestionForm(course_id=session.get('selected_course'))
    if form.validate_on_submit():
        if not session.get('selected_course') or \
        not form.course_id.data == session.get('selected_course'):
            session['selected_course'] = form.course_id.data
        question = Question(body=form.body.data, a=form.a.data,
         b=form.b.data, c=form.c.data,d=form.d.data, e=form.e.data, 
         correct=form.correct.data, course_id=int(session.get('selected_course')),
         user=current_user._get_current_object())
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('main.create_question'))
    return render_template('create_or_edit_question.html', form=form)

@main.route('/my-questions', methods=['GET', 'POST'])
@login_required
@requires_teacher
def my_questions():
    my_questions = Question.query.filter_by(user=current_user._get_current_object())
    return render_template('my_questions.html', my_questions=my_questions)

@main.route('/edit-question/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_teacher
def edit_question(id):
    if not current_user.owns_question(id):
        flash('The question you tried to edit was not created by you')
        return redirect(url_for('main.index'))
    
    question = Question.query.get_or_404(id)
    form = QuestionForm()
    if form.validate_on_submit():
        question.body = form.body.data
        question.a = form.a.data
        question.b = form.b.data
        question.c = form.c.data
        question.d = form.d.data
        question.e = form.e.data
        question.correct = form.correct.data
        question.course_id = form.course_id.data
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('main.my_questions'))
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
    if not current_user.owns_question(id):
        flash('The question you tried to delete was not created by you')
        return redirect(url_for('main.index'))
    question = Question.query.get_or_404(id)
    if question:
        db.session.delete(question)
        db.session.commit()
        return redirect(url_for('main.my_questions'))

@main.route('/course/<int:id>', methods=['GET', 'POST'])
def course(id):
    quizes = Question.query.filter_by(course_id=id)
    if quizes.first() is None:
        flash('There are no questions for this course yet')
        return redirect(url_for('main.index'))
    course_name = quizes.first().course.course_name
    teacher_names = {quiz.user.username for quiz in quizes}
    return render_template('course.html', teacher_names=teacher_names, 
    course_name=course_name, id=id)

@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    cname = request.args.get('cname')
    tname = request.args.get('tname')
    every_quiz = Question.query.all()
    quizes = [quiz for quiz in every_quiz if 
                (quiz.user.username == tname) and (quiz.course.course_name == cname)]
    if request.method == 'POST':
        score = 0
        answered_questions = list(request.form)
        if answered_questions:
            for answered_question in answered_questions:
                if Question.query.get_or_404(answered_question).correct == \
                request.form.get(answered_question):
                    score += 1
        flash(f'Your score was {score}')
        return redirect(url_for('main.quiz', cname=cname, tname=tname))
    return render_template('quiz.html', quizes=quizes, cname=cname, tname=tname)