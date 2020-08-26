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

    def insert_course(self, course_name='default'):
        return self.client.post('/courses', data={
            'course_name' : course_name
        }, follow_redirects=True)
    
    def insert_multiple_choice_question(self):
        return self.client.post('/create-question', data={
            'body':'a',
            'a':'a',
            'b':'b',
            'c':'c',
            'd':'d',
            'e':'e',
            'correct':'a',
            'course_id':1,
            'user_id':1
        }, follow_redirects=True)

    def insert_structural_question(self):
        return self.client.post('/create-question', data={
            'body':'a',
            'a':'a',
            'correct':'a',
            'course_id':1,
            'user_id':1
        }, follow_redirects=True)

    def edit_question_to_structural(self, id):
        return self.client.post(f'/edit-question/{id}', data={
            'body':'aa',
            'a':'aa',
            'correct':'a',
            'course_id': id
        }, follow_redirects=True)
    
    def edit_question_to_multiple_choice(self, id):
        return self.client.post(f'/edit-question/{id}', data={
            'body':'aa',
            'a':'aa',
            'b':'bb',
            'correct':'a',
            'course_id': id
        }, follow_redirects=True)

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Hi' in response.get_data(as_text=True))

    def test_register_login_logout(self):
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

    def test_delete_course(self):
        self.register('student', 'student')
        self.register('teacher', 'teacher')
        User.query.filter_by(username='teacher').first().make_teacher()
        self.login('teacher', 'teacher')
        self.insert_course('Biology')
        self.logout()

        anonymous_response = self.client.get('/delete-course/1', follow_redirects=True)
        self.assertTrue('Please log in to access this page.' \
         in anonymous_response.get_data(as_text=True))
        
        self.login('student', 'student')
        student_response = self.client.get('/delete-course/1', follow_redirects=True)
        self.assertFalse('form' in student_response.get_data(as_text=True))
        self.logout()

        self.login('teacher', 'teacher')
        teacher_response = self.client.get('/delete-course/1', follow_redirects=True)
        self.assertTrue('Course deleted' in teacher_response.get_data(as_text=True))

    def test_course(self):
        self.register('teacher', 'teacher')
        User.query.filter_by(username='teacher').first().make_teacher()
        self.login('teacher', 'teacher')
        self.insert_course('Biology')
        response = self.client.get('/course/1', follow_redirects=True)
        self.assertTrue('There are no questions for this course yet' \
        in response.get_data(as_text=True))

        self.insert_multiple_choice_question()
        response = self.client.get('/course/1', follow_redirects=True)
        self.assertTrue('Biology Course' in response.get_data(as_text=True))

    def test_create_edit_delete_question(self):
        response = self.client.get('/create-question')
        self.assertFalse('form' in response.get_data(as_text=True))

        self.register('student', 'student')
        self.login('student', 'student')
        response = self.client.get('/create-question')
        self.assertFalse('form' in response.get_data(as_text=True))
        self.logout()

        self.register('teacher', 'teacher')
        self.register('teacher2', 'teacher2')
        User.query.filter_by(username='teacher').first().make_teacher()
        User.query.filter_by(username='teacher2').first().make_teacher()
        self.login('teacher', 'teacher')
        response = self.client.get('/create-question')
        self.assertTrue('form' in response.get_data(as_text=True))
        self.insert_course()
        response = self.insert_multiple_choice_question()
        self.assertTrue('A multiple choice question has been created by you' \
         in response.get_data(as_text=True))
        response = self.insert_structural_question()
        self.assertTrue('A structural question has been created by you' \
         in response.get_data(as_text=True))
        self.logout()

        self.login('teacher2', 'teacher2')
        response = self.client.get('/edit-question/1', follow_redirects=True)
        self.assertTrue('The question you tried to edit was not created by you' \
         in response.get_data(as_text=True))
        self.logout()

        self.login('teacher', 'teacher')
        response = self.edit_question_to_structural(1)
        # print(response.get_data(as_text=True))
        self.assertTrue('Question edited and is now a structural question' \
         in response.get_data(as_text=True))

        response = self.edit_question_to_multiple_choice(1)
        # print(response.get_data(as_text=True))
        self.assertTrue('Question edited and is now a multiple choice question' \
         in response.get_data(as_text=True))
        self.logout()

        self.login('teacher2', 'teacher2')
        response = self.client.get('/delete/1', follow_redirects=True)   
        self.assertTrue('The question you tried to delete was not created by you' \
         in response.get_data(as_text=True))  
        self.logout()

        self.login('teacher', 'teacher')
        response = self.client.get('/delete/1', follow_redirects=True)   
        self.assertTrue('Question deleted' in response.get_data(as_text=True))
        
    def test_my_questions(self):
        response = self.client.get('/my-questions')
        self.assertFalse('My questions' in response.get_data(as_text=True))

        self.register('student', 'student')
        self.login('student', 'student')
        response = self.client.get('/my-questions')
        self.assertFalse('My questions' in response.get_data(as_text=True))

        self.register('teacher', 'teacher')
        User.query.filter_by(username='teacher').first().make_teacher()
        self.login('teacher', 'teacher')
        response = self.client.get('/my-questions')
        self.assertTrue('My questions' in response.get_data(as_text=True))
        
        self.insert_course()
        self.insert_multiple_choice_question()
        response = self.client.get('/my-questions')
        self.assertTrue('Edit' in response.get_data(as_text=True))
        self.assertTrue('Delete' in response.get_data(as_text=True))