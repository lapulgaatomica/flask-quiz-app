from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,SubmitField
from wtforms.validators import DataRequired, Length
from wtforms import ValidationError
from ..models import Course
from flask import session

class QuestionForm(FlaskForm):
    body = TextAreaField('Question', validators=[DataRequired(), Length(1, 256)])
    a = StringField('First Option', validators=[DataRequired(), Length(1, 128)])
    b = StringField('Second Option', validators=[DataRequired(), Length(1, 128)])
    c = StringField('Third Option')
    d = StringField('Fourth Option')
    e = StringField('Fifth Option')
    correct = SelectField('Correct Option', choices=[
        ('a', 'First Option'), ('b', 'Second Option'),
        ('c', 'Third Option'), ('d', 'Fourth Option'), 
        ('e', 'Fifth Option')])
    course_id = SelectField('Course', coerce=int)
    submit = SubmitField('Submit Question')

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.course_id.choices = [(course.id, course.course_name) for course in Course.query.all()]

class CoursesForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField('Enter Course Name')