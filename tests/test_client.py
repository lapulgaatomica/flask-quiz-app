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

    def test_register_and_login(self):
        #register a new account
        response = self.client.post('/auth/register', data={
            'username' : 'ran',
            'password' : 'ran',
            'password2' : 'ran'
        })
        self.assertEqual(response.status_code, 302)

        #login with the new account
        response = self.client.post('/auth/login', data={
            'username' : 'ran',
            'password' : 'ran'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('ran', response.get_data(as_text=True)))
        self.assertTrue(
            'You have just been logged in.' in response.get_data(
                as_text=True))
        
        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have just been logged out' in response.get_data(
            as_text=True))