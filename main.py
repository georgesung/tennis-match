#!/usr/bin/env python

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

# [START handlers]
class MainPage(webapp2.RequestHandler):
    def get(self):
        self.redirect('/login')

class Login(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'user': 'xzy',
            'greetings': 'abc',
        }
        template = JINJA_ENVIRONMENT.get_template('login.html')
        self.response.write(template.render(template_values))

class SignUp(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'user': 'xzy',
            'greetings': 'abc',
        }
        template = JINJA_ENVIRONMENT.get_template('signup.html')
        self.response.write(template.render(template_values))

class Dashboard(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'user': 'xzy',
            'greetings': 'abc',
        }
        template = JINJA_ENVIRONMENT.get_template('dashboard.html')
        self.response.write(template.render(template_values))
# [END handlers]

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', Login),
    ('/signup', SignUp),
    ('/dashboard', Dashboard),
], debug=True)
# [END app]
