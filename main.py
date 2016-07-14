'''
The API backend
'''

from datetime import datetime
from datetime import timedelta
from eastern_tzinfo import Eastern_tzinfo
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
from models import StringMsg
from models import BooleanMsg

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

		# Normalize NTRP if needed
		ntrp = profile.ntrp
		if profile.gender == 'f':
			ntrp = profile.ntrp - 0.5

		# Add default values for those missing
		data['players']   = [user_id]
		data['confirmed'] = False
		data['ntrp']      = ntrp

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


	@ndb.transactional(xg=True)
	def _joinMatch(self, request):
		"""Join an available Match, given Match's key.
		If there is mid-air collision, return false. If successful, return true."""

		# Preload necessary data items
		user = endpoints.get_current_user()
		if not user:
			raise endpoints.UnauthorizedException('Authorization required')
		user_id = user.email()

		# If any field in request is None, then raise exception
		if request.data is None:
			raise endpoints.BadRequestException('Need match ID from request.data')

		# Get match key, then get the Match entity from db
		match_key = request.data
		match = ndb.Key(urlsafe=match_key).get()

		# Make sure match is not full. If full, return false.
		match_full = False
		if match.singles and len(match.players) >= 2:
			match_full = True
		elif not match.singles and len(match.players) >= 4:
			match_full = True

		if match_full:
			status = BooleanMsg()
			status.data = False
			return status

		# Update 'players' and 'confirmed' fields (if needed)
		match.players.append(user_id)

		if match.singles or len(match.players) >= 4:
			match.confirmed = True

		# Update Match db
		match.put()

		# Add current match key to current user's matches list
		profile_key = ndb.Key(Profile, user.email())
		profile = profile_key.get()
		profile.matches.append(match_key)
		profile.put()

		# Return true, for success
		status = BooleanMsg()
		status.data = True

		return status

	@endpoints.method(StringMsg, BooleanMsg, path='',
		http_method='POST', name='joinMatch')
	def joinMatch(self, request):
		"""Join an available Match, given Match's key"""
		return self._joinMatch(request)


	@ndb.transactional(xg=True)
	def _cancelMatch(self, request):
		"""Cancel an existing Match, given Match's key.
		If successful, return true. Fail condition?"""

		# Preload necessary data items
		user = endpoints.get_current_user()
		if not user:
			raise endpoints.UnauthorizedException('Authorization required')
		user_id = user.email()

		# If any field in request is None, then raise exception
		if request.data is None:
			raise endpoints.BadRequestException('Need match ID from request.data')

		# Get match key, then get the Match entity from db
		match_key = request.data
		match = ndb.Key(urlsafe=match_key).get()

		# If cancelling player is the "owner" of the match and match has >1 player,
		# find new owner to update Match's ntrp
		if match.players[0] == user_id and len(match.players) > 1:
			new_owner = ndb.Key(Profile, match.players[1]).get()

			ntrp = new_owner.ntrp
			if new_owner.gender == 'f':
				ntrp -= 0.5

			match.ntrp = ntrp

		# Update 'players' and 'confirmed' fields (if needed)
		match.players.remove(user_id)
		match.confirmed = False

		# Update Match in ndb
		if len(match.players) == 0:
			match.key.delete()
		else:
			match.put()

		# Remove current match key from current user's matches list
		profile_key = ndb.Key(Profile, user.email())
		profile = profile_key.get()
		profile.matches.remove(match_key)
		profile.put()

		# Return true, for success (how can it fail?)
		status = BooleanMsg()
		status.data = True

		return status

	@endpoints.method(StringMsg, BooleanMsg, path='',
		http_method='POST', name='cancelMatch')
	def cancelMatch(self, request):
		"""Cancel an existing Match, given Match's key"""
		return self._cancelMatch(request)


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

	def _appendMatchesMsg(self, match, matches_msg):
		# Ignore matches in the past, or matches that will occur in less than 30 minutes
		# Note we store matches in naive time, but datetime.now() returns UTC time,
		# so we use tzinfo object to convert to local time
		if match.dateTime - timedelta(minutes=30) < datetime.now(Eastern_tzinfo()).replace(tzinfo=None):
			return

		# Convert datetime object into separate date and time strings
		date, time = match.dateTime.strftime('%m/%d/%Y|%H:%M').split('|')

		# Convert match.players into pipe-separated 'firstName lastName' string
		# e.g. ['Bob Smith|John Doe|Alice Wonderland|Foo Bar', 'Blah Blah|Hello World']
		players = ''
		for player_id in match.players:
			player_profile = ndb.Key(Profile, player_id).get()

			first_name  = player_profile.firstName
			last_name   = player_profile.lastName
			ntrp        = player_profile.ntrp
			gender      = player_profile.gender.capitalize()

			players += first_name + ' ' + last_name + ' (' + str(ntrp) + gender + '), '
		players = players.rstrip(', ')

		# Populate fields in matches_msg
		matches_msg.singles.append(match.singles)
		matches_msg.date.append(date)
		matches_msg.time.append(time)
		matches_msg.location.append(match.location)
		matches_msg.players.append(players)
		matches_msg.confirmed.append(match.confirmed)
		matches_msg.key.append(match.key.urlsafe())

		# No need to return anything, matches_msg is a reference, so you modified the original thing


	@endpoints.method(message_types.VoidMessage, MatchesMsg,
			path='', http_method='GET', name='getMyMatches')
	def getMyMatches(self, request):
		"""Get all confirmed or pending matches for current user."""
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

			self._appendMatchesMsg(match, matches_msg)

		return matches_msg

	@endpoints.method(message_types.VoidMessage, MatchesMsg,
			path='', http_method='GET', name='getAvailableMatches')
	def getAvailableMatches(self, request):
		"""
		Get all available matches for current user.
		Search through DB to find partners of similar skill.
		"""
		user = endpoints.get_current_user()

		if not user:
			raise endpoints.UnauthorizedException('Authorization required')

		# Get user Profile based on userId (email)
		profile = ndb.Key(Profile, user.email()).get()

		# Create new MatchesMsg message
		matches_msg = MatchesMsg()

		# Women's NTRP is equivalent to -0.5 men's NTRP, from empirical observation
		my_ntrp = profile.ntrp
		if profile.gender == 'f':
			my_ntrp -= 0.5

		# Query the DB to find matches where partner is of similar skill
		query = Match.query(ndb.OR(Match.ntrp == my_ntrp, Match.ntrp == my_ntrp + 0.5, Match.ntrp == my_ntrp - 0.5))
		query = query.order(Match.dateTime)  # ascending datetime order (i.e. earliest matches first)

		for match in query:
			# Ignore matches current user is already participating in
			if profile.userId in match.players:
				continue

			self._appendMatchesMsg(match, matches_msg)

		return matches_msg


# registers API
api = endpoints.api_server([TennisApi])
