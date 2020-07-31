from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user

def requires_teacher(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_teacher:
            # abort(403)
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function