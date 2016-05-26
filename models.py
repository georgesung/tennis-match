'''
Models
'''

import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class Profile(ndb.Model):
	"""Profile -- User profile object"""
	userId = ndb.StringProperty()
	firstName = ndb.StringProperty()
	lastName = ndb.StringProperty()


class ProfileForm(messages.Message):
	"""ProfileForm -- Profile outbound form message"""
	userId = messages.StringField(1)
	firstName = messages.StringField(2)
	lastName = messages.StringField(3)
