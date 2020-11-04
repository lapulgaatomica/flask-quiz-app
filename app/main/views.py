from . import main
from flask import render_template, redirect, url_for, session, request, flash
from .forms import QuestionForm, CoursesForm
from flask_login import login_required, current_user
from ..decorators import requires_teacher
from ..models import Course, Question, Result, User
from .. import db
from sqlalchemy.sql.expression import func

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
            flash(f'A Course named {form.course_name.data} has been created by you')
            return redirect(url_for('main.courses'))
        return render_template('courses.html', form=form, courses=courses)
    return render_template('courses.html', courses=courses)

@main.route('/delete-course/<int:id>', methods=['GET'])
@login_required
@requires_teacher
def delete_course(id):
    course = Course.query.get_or_404(id)
    if course:
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted')
        return redirect(url_for('main.courses'))

@main.route('/course/<int:id>', methods=['GET'])
def course(id):
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
    #sets the default course in the course select field
    form = QuestionForm(course_id=session.get('selected_course'))
    if form.validate_on_submit():
        #if there is no selected course in the session or
        #if the course that was just selected is not the course that was in the session
        #change the course in the session to the one just selected
        if not session.get('selected_course') or \
        not form.course_id.data == session.get('selected_course'):
            session['selected_course'] = form.course_id.data
        question = Question(
            body=form.body.data,
            a=form.a.data,
            b=form.b.data,
            c=form.c.data if form.b.data else None,
            d=form.d.data if form.b.data else None,
            e=form.e.data if form.b.data else None, 
            correct=form.correct.data,
            course_id=int(session.get('selected_course')),
            user=current_user._get_current_object(),
            is_structural=False if form.b.data else True)
        db.session.add(question)
        db.session.commit()
        flash(f'A multiple choice question has been created by you') if form.b.data else \
        flash(f'A structural question has been created by you')
        return redirect(url_for('main.create_question'))
    return render_template('create_or_edit_question.html', form=form)

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
        question.c = form.c.data if form.b.data else None
        question.d = form.d.data if form.b.data else None
        question.e = form.e.data if form.b.data else None
        question.correct = form.correct.data
        question.course_id = form.course_id.data
        question.is_structural = False if form.b.data else True
        db.session.add(question)
        db.session.commit()
        flash('Question edited and is now a multiple choice question') if form.b.data else\
        flash('Question edited and is now a structural question')
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
        flash('Question deleted')
        return redirect(url_for('main.my_questions'))

@main.route('/my-questions', methods=['GET'])
@login_required
@requires_teacher
def my_questions():
    my_questions = Question.query.filter_by(user=current_user._get_current_object())
    return render_template('my_questions.html', my_questions=my_questions)

@main.route('/quiz', methods=['GET', 'POST'])
def quiz():
    course = request.args.get('course')
    teacher = request.args.get('teacher')
    quizes = Question.query.filter_by(course_id=course).filter_by(user_id=teacher).order_by(func.random()).limit(10)
    tname = quizes.first().user.username
    cname = quizes.first().course.course_name
    if request.method == 'POST':
        score = 0
        answered_questions = list(request.form)
        if answered_questions:
            for answered_question in answered_questions:
                my_answer = request.form.get(answered_question)
                query_result = Question.query.get_or_404(answered_question)
                if (not query_result.is_structural) and (query_result.correct == my_answer):
                    score += 1
                elif (query_result.is_structural) and (query_result.a.lower() == my_answer.lower()):
                    score += 1
        
        if current_user.is_authenticated:
            result = Result.query.filter_by(user_id=current_user.id).filter_by(course_id=course).filter_by(teacher_id=teacher).first()
            if result is None:
                result = Result(
                course_id=course,
                user=current_user,
                teacher_id=teacher,
                highest_score=score)
                flash(f'Your highest score in this quiz is {score} which is also your score in the test')
            else:
                if score > result.highest_score:
                    result.highest_score = score
                    flash(f'Your highest score in this quiz is {score} which is also your score in the test')
                else:
                    flash(f'Your score in this quiz is {score} ')
            db.session.add(result)
            db.session.commit()
        else:
            flash(f'Your score in this quiz is {score} ')
        return redirect(url_for('main.quiz', course=course, teacher=teacher))
    return render_template('quiz.html', quizes=quizes, cname=cname, tname=tname)

@main.route('/my-results', methods=['GET'])
@login_required
def my_results():
    my_results = Result.query.filter_by(user=current_user._get_current_object()).all()
    for my_result in my_results:
        my_result.teacher_name = User.query.get_or_404(my_result.teacher_id).username 
    return render_template('my_results.html', my_results=my_results)