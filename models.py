'''
Models
'''

import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class Profile(ndb.Model):
	"""Profile -- User profile object"""
	userId = ndb.StringProperty()
	mainEmail = ndb.StringProperty()
	#teeShirtSize = ndb.StringProperty(default='NOT_SPECIFIED')
	firstName = ndb.StringProperty()
	lastName = ndb.StringProperty()


class ProfileForm(messages.Message):
	"""ProfileForm -- Profile outbound form message"""
	userId = messages.StringField(1)
	mainEmail = messages.StringField(2)
	firstName = messages.StringField(3)
	lastName = messages.StringField(4)
