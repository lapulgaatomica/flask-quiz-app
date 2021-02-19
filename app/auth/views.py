from flask import render_template, redirect, url_for, flash
from .forms import RegistrationForm, LoginForm
from . import auth
from .. import db
from ..models import User
from flask_login import login_user, logout_user, login_required

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    The function that registers a new user

    return: the template to register if the
    request method is a get request, or a
    redirect to the login route if the request
    is a post request
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user_exists = User.query.filter_by(username=form.username.data.lower()).first()
        if user_exists:
            flash(f'username {form.username.data} already exists')
            return render_template('auth/register.html', form=form)
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You have just been registered.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Function to login the user
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=True)
            flash('You have just been logged in.')
            return redirect(url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """
    Function to log the user out
    """
    logout_user()
    flash('You have just been logged out')
    return redirect(url_for('auth.login'))