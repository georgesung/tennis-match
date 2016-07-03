'''
The API backend
'''

from datetime import datetime
import json
import os

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Profile
from models import ProfileMsg
from models import Match
from models import MatchMsg
from models import MatchesMsg

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

	@ndb.transactional(xg=True)
	def _createMatch(self, request):
		"""Create new Match, update user Profile to add new Match to Profile.
		Returns MatchMsg/request."""

		# Preload necessary data items
		user = endpoints.get_current_user()
		if not user:
			raise endpoints.UnauthorizedException('Authorization required')
		user_id = user.email()

		# If any field in request is None, then raise exception
		if any([getattr(request, field.name) is None for field in request.all_fields()]):
			raise endpoints.BadRequestException('All input fields required to create a match')

		# Copy MatchMsg/ProtoRPC Message into dict
		data = {field.name: getattr(request, field.name) for field in request.all_fields()}

		# Get user profile from NDB
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# Add default values for those missing
		data['players']   = [user_id]
		data['confirmed'] = False
		data['ntrp']      = profile.ntrp

		# Convert date/time from string to datetime object
		dt_string = data['date'] + '|' + data['time']
		data['dateTime'] = datetime.strptime(dt_string, '%m/%d/%Y|%H:%M')
		del data['date']
		del data['time']

		# Create new match based on data, and put in datastore
		match_key = Match(**data).put()

		# Update user profile, adding the new match to Profile.matches
		profile.matches.append(match_key.urlsafe())
		profile.put()

		return request

	@endpoints.method(MatchMsg, MatchMsg, path='',
		http_method='POST', name='createMatch')
	def createMatch(self, request):
		"""Create new Match"""
		return self._createMatch(request)


	###################################################################
	# Profile objects
	###################################################################

	def _copyProfileToForm(self, prof):
		"""Copy relevant fields from Profile to ProfileMsg."""
		pf = ProfileMsg()
		for field in pf.all_fields():
			if hasattr(prof, field.name):
				setattr(pf, field.name, getattr(prof, field.name))
		pf.check_initialized()
		return pf

	@endpoints.method(message_types.VoidMessage, ProfileMsg,
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

	@endpoints.method(ProfileMsg, ProfileMsg,
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

	###################################################################
	# Queries
	###################################################################

	@endpoints.method(message_types.VoidMessage, MatchesMsg,
			path='', http_method='GET', name='getMyMatches')
	def getMyMatches(self, request):
		"""Return user profile."""
		user = endpoints.get_current_user()

		if not user:
			raise endpoints.UnauthorizedException('Authorization required')

		# Get user Profile based on userId (email)
		profile = ndb.Key(Profile, user.email()).get()

		# Create new MatchesMsg message
		matches_msg = MatchesMsg()

		# For each match is user's matches, add the info to match_msg
		for match_key in profile.matches:
			match = ndb.Key(urlsafe=match_key).get()

			# Convert datetime object into separate date and time strings
			date, time = match.dateTime.strftime('%m/%d/%Y|%H:%M').split('|')

			# Convert match.players into pipe-separated 'firstName lastName' string
			# e.g. ['Bob Smith|John Doe|Alice Wonderland|Foo Bar', 'Blah Blah|Hello World']
			players = ''
			for player_id in match.players:
				player_profile = ndb.Key(Profile, player_id).get()

				first_name = player_profile.firstName
				last_name = player_profile.lastName

				players += first_name + ' ' + last_name + '|'
			players = players.rstrip('|')

			# Populate fields in matches_msg
			matches_msg.singles.append(match.singles)
			matches_msg.date.append(date)
			matches_msg.time.append(time)
			matches_msg.location.append(match.location)
			matches_msg.players.append(players)
			matches_msg.confirmed.append(match.confirmed)
			matches_msg.match_keys.append(match_key)

		print(matches_msg)  # DEBUG

		return matches_msg


# registers API
api = endpoints.api_server([TennisApi])
