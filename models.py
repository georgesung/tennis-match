'''
Models

If you need to update the model schema live, see:
https://cloud.google.com/appengine/articles/update_schema
'''

import endpoints
from protorpc import messages
from google.appengine.ext import ndb


class Profile(ndb.Model):
	"""Profile -- User profile object"""
	userId        = ndb.StringProperty()
	contactEmail  = ndb.StringProperty()
	firstName     = ndb.StringProperty(default='')
	lastName      = ndb.StringProperty(default='')
	gender        = ndb.StringProperty(default='m')  # m/f
	ntrpRating    = ndb.FloatProperty(default=3.5)


class ProfileForm(messages.Message):
	"""ProfileForm -- Profile outbound form message"""
	userId        = messages.StringField(1)
	contactEmail  = messages.StringField(2)
	firstName     = messages.StringField(3)
	lastName      = messages.StringField(4)
	gender        = messages.StringField(5)  # m/f
	ntrpRating    = messages.FloatField(6)
