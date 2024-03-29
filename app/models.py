from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    a = db.Column(db.String(128), nullable=False)
    b = db.Column(db.String(128))
    c = db.Column(db.String(128))
    d = db.Column(db.String(128))
    e = db.Column(db.String(128))
    correct = db.Column(db.String(1), nullable=False)
    is_structural = db.Column(db.Boolean, default=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<{self.body}>'

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    highest_score = db.Column(db.Integer, default=0)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_teacher = db.Column(db.Boolean, default=False)
    courses = db.relationship('Question', backref='user', foreign_keys=[Question.user_id], lazy='dynamic', cascade="all, delete-orphan")
    results = db.relationship('Result', backref='user', foreign_keys=[Result.user_id], lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<{self.username}>'

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.is_teacher is None:
            if self.username == current_app.config['HEADTEACHER']:
                self.is_teacher = True

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def owns_question(self, id):
        return self.id == Question.query.get_or_404(id).user.id
    
    def make_teacher(self):
        self.is_teacher = True

class AnonymousUser(AnonymousUserMixin):
    is_teacher = False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(64), unique=True)
    questions = db.relationship('Question', backref='course', lazy='dynamic', cascade="all, delete-orphan")
    results = db.relationship('Result', backref='course', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<{self.course_name}>'