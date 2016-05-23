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
		# copy relevant fields from Profile to ProfileForm
		pf = ProfileForm()
		for field in pf.all_fields():
			if hasattr(prof, field.name):
				setattr(pf, field.name, getattr(prof, field.name))
		pf.check_initialized()
		return pf

	@endpoints.method(message_types.VoidMessage, ProfileForm,
			path='dashboard', http_method='GET', name='getProfile')
	def getProfile(self, request):
		"""Return user profile."""
		user = endpoints.get_current_user()

		print user

		if not user:
			raise endpoints.UnauthorizedException('Authorization required')

		profile = Profile(
			userId = 'user_id placeholder~~~',
			displayName = user.nickname(),
			mainEmail= user.email(),
		)

		return self._copyProfileToForm(profile)

# registers API
api = endpoints.api_server([TennisApi])
