'''
The API backend
'''

from datetime import datetime
import json
import os
import time

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
	"""Tennis API v0.1"""

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

		print('gsung: user.email() = ' + user.email())  # DEBUG

		# Create new ndb key based on unique user ID (email)
		# Get profile from datastore -- if profile not found, then profile=None
		profile_key = ndb.Key(Profile, user.email())
		profile = profile_key.get()

		# Create placeholder empty profile if user does not have one, and put it in datastore
		if not profile:
			profile = Profile(
				key = profile_key,
				userId = user.email(),
				firstName = '',
				lastName = '',
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
				setattr(profile, field.name, str(getattr(request, field.name)))

		# Save updated profile to datastore
		profile.put()

		return self._copyProfileToForm(profile)

# registers API
api = endpoints.api_server([TennisApi])
