from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def requires_teacher(f):
    """
    Decorator to ensure that a user accesing a
    function invoked by calling by a route is a teacher

    :return: a redirect if the current user accessing the
    route that called the function wrapped by this decorator
    is not a teacher, else the function that was called is
    returned
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_teacher:
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function