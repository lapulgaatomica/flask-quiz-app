import re
import unittest
from app import create_app, db
from app.models import User

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Hi' in response.get_data(as_text=True))

    def register(self, username, password):
        return self.client.post('/auth/register', data={
            'username' : username,
            'password' : password,
            'password2' : password
        })
    
    def login(self, username, password):
        return self.client.post('/auth/login', data={
            'username' : username,
            'password' : password
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def insert_course(self, course_name):
        return self.client.post('/courses', data={
            'course_name' : course_name
        }, follow_redirects=True)

    def test_register_and_login(self):
        #register a new account
        register_response = self.register('test', 'test')
        self.assertEqual(register_response.status_code, 302)

        #login with the new account
        login_response = self.login('test', 'test')
        self.assertEqual(login_response.status_code, 200)
        self.assertTrue(
            'You have just been logged in.' in login_response.get_data(
                as_text=True))
        self.assertTrue(re.search('Hi\s+test!', login_response.get_data(as_text=True)))
        
        # log out
        logout_response = self.logout()
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue('You have just been logged out' in logout_response.get_data(
            as_text=True))

    def test_courses_route(self):
        self.register('student', 'student')
        self.login('student', 'student')
        student_response = self.client.get('/courses')
        self.assertEqual(student_response.status_code, 200)
        self.assertFalse('form' in student_response.get_data(as_text=True))
        insert_course_response = self.insert_course('Biology')
        self.assertFalse('biology' in insert_course_response.get_data(as_text=True))
        self.logout()

        self.register('teacher', 'teacher')
        User.query.filter_by(username='teacher').first().make_teacher()
        self.login('teacher', 'teacher')
        response = self.client.get('/courses')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.get_data(as_text=True))
        insert_course_response = self.insert_course('Biology')
        self.assertTrue('biology' in insert_course_response.get_data(as_text=True))
        insert_course_response = self.insert_course('Biology')
        self.assertTrue('A Course named Biology already exists' \
         in insert_course_response.get_data(as_text=True))