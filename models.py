'''
Models

If you need to update the model schema live, see:
https://cloud.google.com/appengine/articles/update_schema
'''

import endpoints
from protorpc import messages
from google.appengine.ext import ndb

import datetime

# User profile, and its messages
class Profile(ndb.Model):
	userId        = ndb.StringProperty(required=True)
	contactEmail  = ndb.StringProperty()
	firstName     = ndb.StringProperty(default='')
	lastName      = ndb.StringProperty(default='')
	gender        = ndb.StringProperty(default='m')  # m/f
	ntrpRating    = ndb.FloatProperty(default=3.5)

class ProfileForm(messages.Message):
	userId        = messages.StringField(1)
	contactEmail  = messages.StringField(2)
	firstName     = messages.StringField(3)
	lastName      = messages.StringField(4)
	gender        = messages.StringField(5)  # m/f
	ntrpRating    = messages.FloatField(6)


# Match object, and its messages
class Match(ndb.Model):
	# TODO: Ancestor?
	singles = ndb.BooleanProperty(required=True)
	dateTime = ndb.DateTimeProperty(required=True)
	location = ndb.GeoPtProperty(required=True)
	players = ndb.StringProperty(repeated=True)  # TODO: Store userId key? Or just plain userId?

class MatchForm(messages.Message):
	singles = messages.BooleanField(1)
	dateTime = messages.StringField(2)
	location = messages.StringField(3)
	players = messages.StringField(4, repeated=True)