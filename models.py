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
	ntrp          = ndb.FloatProperty(default=3.5)
	matches       = ndb.StringProperty(repeated=True)  # match keys (store urlsafe version), dynamically changing

class ProfileForm(messages.Message):
	userId        = messages.StringField(1)
	contactEmail  = messages.StringField(2)
	firstName     = messages.StringField(3)
	lastName      = messages.StringField(4)
	gender        = messages.StringField(5)  # m/f
	ntrp          = messages.FloatField(6)


# Match object, and its messages
class Match(ndb.Model):
	# TODO: Ancestor?
	singles   = ndb.BooleanProperty(required=True)
	dateTime  = ndb.DateTimeProperty(required=True)
	location  = ndb.StringProperty(required=True)  # no need for GeoPtProperty
	players   = ndb.StringProperty(repeated=True)  # userIds
	confirmed = ndb.BooleanProperty(required=True)
	ntrp      = ndb.FloatProperty(required=True)  # NTRP rating of creator of match

class MatchForm(messages.Message):
	singles   = messages.BooleanField(1)
	date      = messages.StringField(2)
	time      = messages.StringField(3)
	location  = messages.StringField(4)
	players   = messages.StringField(5, repeated=True)
	confirmed = messages.BooleanField(6)
	ntrp      = messages.FloatField(7)

