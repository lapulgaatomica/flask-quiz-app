import os
import click
from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Course, Question, Result
from flask import g

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """
    Ensures returned values are accessible in the interactive shell
    without importing them.

    :return: a dictionary of values(Mostly database tables) to be imported
    """
    return dict(db=db, User=User, Course=Course, Question=Question, Result=Result)

@app.context_processor
def get_courses():
    """
    Ensures all the courses in the database are available in any templates that calls g.courses

    :return: a dictionary of courses to be used by all templates
    """
    g.courses = Course.query.order_by('course_name').all()
    return dict(courses=g.courses)

@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.cli.command()
def deploy():
    """
    Run deployment tasks.
    """
    # migrate database to latest database revision
    upgrade()
