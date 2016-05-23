'''
Models
'''

import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class Profile(ndb.Model):
	"""Profile -- User profile object"""
	userId = ndb.StringProperty()
	displayName = ndb.StringProperty()
	mainEmail = ndb.StringProperty()
	teeShirtSize = ndb.StringProperty(default='NOT_SPECIFIED')


class ProfileForm(messages.Message):
	"""ProfileForm -- Profile outbound form message"""
	userId = messages.StringField(1)
	displayName = messages.StringField(2)
	mainEmail = messages.StringField(3)
