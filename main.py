'''
The API backend
'''

from datetime import datetime
import json
import os
import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Profile
from models import ProfileForm

from settings import WEB_CLIENT_ID

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@endpoints.api( name='tennis',
				version='v1',
				allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
				scopes=[EMAIL_SCOPE])
class TennisApi(remote.Service):
	"""Tennis API"""

	###################################################################
	# Match objects
	###################################################################

	@ndb.transactional()
	def _createMatch(self, request):
		"""Create new Match, update user Profile to add new Match to Profile.
		Returns MatchForm/request."""

		# Preload necessary data items
		user = endpoints.get_current_user()
		if not user:
			raise endpoints.UnauthorizedException('Authorization required')
		user_id = getUserId(user)

		if not (request.singles and request.date and request.time and request.location):
			raise endpoints.BadRequestException('All input fields required to create a match')

		# Copy MatchForm/ProtoRPC Message into dict
		data = {field.name: getattr(request, field.name) for field in request.all_fields()}
		print(data)  # DEBUG

		# Add default values for those missing
		data[players] = [user_id]
		data[confirmed] = False

		# Convert date/time from string to datetime object
		# TODO: Make sure the format is consistent
		data['dateTime'] = datetime.strptime(data['dateTime'], "%Y-%m-%d").date()

		# Find Profile key based on user ID
		# Generate Match ID based on Profile key
		# Generate Match NDB key based on Match ID
		profile_key = ndb.Key(Profile, user_id)
		match_id = Match.allocate_ids(size=1, parent=profile_key)[0]
		match_key = ndb.Key(Match, match_id, parent=profile_key)

		# Explicitly set the key for the new Match entity
		data['key'] = match_key

		# Create match, add it to datastore
		Match(**data).put()

		# Update user profile, adding the new match to Profile.matches
		profile = profile_key.get()
		profile.matches.append(match_key.urlsafe())
		profile.put()

		return request

	@endpoints.method(MatchForm, MatchForm, path='',
		http_method='POST', name='createMatch')
	def createMatch(self, request):
		"""Create new Match"""
		return self._createMatch(request)


	###################################################################
	# Profile objects
	###################################################################

	def _copyProfileToForm(self, prof):
		"""Copy relevant fields from Profile to ProfileForm."""
		pf = ProfileForm()
		for field in pf.all_fields():
			if hasattr(prof, field.name):
				setattr(pf, field.name, getattr(prof, field.name))
		pf.check_initialized()
		return pf

	@endpoints.method(message_types.VoidMessage, ProfileForm,
			path='', http_method='GET', name='getProfile')
	def getProfile(self, request):
		"""Return user profile."""
		user = endpoints.get_current_user()

		if not user:
			raise endpoints.UnauthorizedException('Authorization required')

		# Create new ndb key based on unique user ID (email)
		# Get profile from datastore -- if profile not found, then profile=None
		profile_key = ndb.Key(Profile, user.email())
		profile = profile_key.get()

		# Create placeholder empty profile if user does not have one, and put it in datastore
		if not profile:
			profile = Profile(
				key = profile_key,
				userId = user.email(),
				contactEmail = user.email(),
			)

			profile.put()

		return self._copyProfileToForm(profile)

	@endpoints.method(ProfileForm, ProfileForm,
			path='', http_method='POST', name='updateProfile')
	def updateProfile(self, request):
		"""Update user profile."""

		# Ensure authentication
		user = endpoints.get_current_user()
		if not user:
			raise endpoints.UnauthorizedException('Authorization required')

		# Make sure the incoming message is initialized, raise exception if not
		request.check_initialized()

		# Get existing profile from datastore
		profile_key = ndb.Key(Profile, user.email())
		profile = profile_key.get()

		# Update profile object from the user's form
		for field in request.all_fields():
			if field.name == 'userId':
				setattr(profile, 'userId', user.email())
			else:
				#setattr(profile, field.name, str(getattr(request, field.name)))
				setattr(profile, field.name, getattr(request, field.name))

		# Save updated profile to datastore
		profile.put()

		return self._copyProfileToForm(profile)

# registers API
api = endpoints.api_server([TennisApi])
