'''
The API backend
'''

from datetime import datetime
from datetime import timedelta
from eastern_tzinfo import Eastern_tzinfo
import json
import os
from django.utils.http import urlquote
import Crypto.Random
from Crypto.Protocol import KDF
import jwt

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Profile
from models import ProfileMsg
from models import CreateAccountMsg
from models import PasswordMsg
from models import Match
from models import MatchMsg
from models import MatchesMsg
from models import StringMsg
from models import BooleanMsg
from models import AccessTokenMsg

# Custom accounts
from settings import CA_SECRET
# Facebook
from settings import FB_APP_ID
from settings import FB_APP_SECRET
from settings import FB_API_VERSION
# Google
from settings import GRECAPTCHA_SECRET
#from settings import WEB_CLIENT_ID
# SparkPost
from settings import SPARKPOST_SECRET

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

@endpoints.api( name='tennis',
				version='v1',
				allowed_client_ids=[API_EXPLORER_CLIENT_ID],
				scopes=[EMAIL_SCOPE])
class TennisApi(remote.Service):
	"""Tennis API"""

	###################################################################
	# Email Management
	###################################################################

	def _emailVerif(self, profile):
		""" Send verification email, given reference to Profile object. Return success True/False. """
		payload = {
			'recipients': [{
				'address': {
					'email': profile.contactEmail,
					'name': profile.firstName + ' ' + profile.lastName,
				},
				'substitution_data': {
					'first_name': profile.firstName,
				},
			}],
			'content': {
				'template_id': 'email-verif',
			},
		}
		payload_json = json.dumps(payload)
		headers = {
			'Authorization': SPARKPOST_SECRET,
			'Content-Type': 'application/json',
		}
		print('partner')  # DEBUG
		# POST to SparkPost API
		url = 'https://api.sparkpost.com/api/v1/transmissions?num_rcpt_errors=3'
		try:
			result = urlfetch.Fetch(url, payload=payload_json, method=2)
		except:
			raise endpoints.BadRequestException('urlfetch error: Unable to POST to SparkPost')
			return False
		print(result)  # DEBUG
		data = json.loads(result.content)
		print(data)  # DEBUG

		# Determine status of email verification from SparkPost, return True/False
		if 'errors' in data:
			return False
		if data['results']['total_accepted_recipients'] != 1:
			return False

		return True


	###################################################################
	# Custom Accounts
	###################################################################

	def _genToken(self, payload):
		""" Generate custom auth JWT token given payload dict """
		secret = CA_SECRET
		return jwt.encode(payload, secret, algorithm='HS256')

	def _decodeToken(self, token):
		""" Decode custom token. If successful, return payload. Else, return None. """
		secret = CA_SECRET
		try:
			return jwt.decode(token, secret, algorithm='HS256')
		except:
			return None

	def _getUserId(self, token):
		""" Get userId: First check if local account, then check if FB account """
		# See if token belongs to custom account user
		ca_payload = self._decodeToken(token)
		if ca_payload is not None:
			return ca_payload['userId']

		# If above failed, try FB token
		return self._getFbUserId(token)


	@endpoints.method(AccessTokenMsg, BooleanMsg, path='',
		http_method='POST', name='verifyToken')
	def verifyToken(self, request):
		""" Verify validity of custom account token, return True (valild) or False (invalid) """
		status = BooleanMsg()  # return status
		status.data = False  # default to invalid (False)

		ca_payload = self._decodeToken(request.accessToken)
		if ca_payload is not None:
			if 'userId' in ca_payload:
				status.data = True

		return status

	@endpoints.method(CreateAccountMsg, StringMsg, path='',
		http_method='POST', name='createAccount')
	def createAccount(self, request):
		""" Create new custom account """
		status = StringMsg()  # return status
		status.data = 'error'  # default to error

		# Verify if user passed reCAPTCHA
		# POST request to Google reCAPTCHA API
		url = 'https://www.google.com/recaptcha/api/siteverify?secret=%s&response=%s' % (GRECAPTCHA_SECRET, request.recaptcha)
		try:
			result = urlfetch.Fetch(url, method=2)
		except:
			raise endpoints.BadRequestException('urlfetch error: Unable to POST to Google reCAPTCHA')
			return status
		data = json.loads(result.content)
		if not data['success']:
			status.data = 'recaptcha_fail'
			return status

		user_id = 'ca_' + request.email

		# Get profile from datastore -- if profile not found, then profile=None
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If profile exists, return status
		if profile:
			status.data = 'user_exists'
			return status

		# Salt and hash the password
		salt = Crypto.Random.new().read(16)
		passkey = KDF.PBKDF2(request.password, salt).encode('hex')

		salt_passkey = salt.encode('hex') + '|' + passkey

		# Create new profile for user
		Profile(
			key = profile_key,
			userId = user_id,
			contactEmail = request.email,
			salt_passkey = salt_passkey,
			loggedIn = True,
		).put()

		# Generate user access token (extra_secret = salt)
		token = self._genToken({'userId': user_id})

		# If we get here, means we suceeded
		status.data = 'success'
		status.accessToken = token
		return status

	@endpoints.method(PasswordMsg, BooleanMsg, path='',
		http_method='POST', name='login')
	def login(self, request):
		""" Check username/password to login """
		status = BooleanMsg()  # return status
		status.data = False  # default to error (False)

		user_id = 'ca_' + request.email

		# Get profile from datastore -- if profile not found, then profile=None
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If profile does not exist, return False
		if not profile:
			return status

		# Parse salt and passkey from DB, compare it to provided version
		db_salt, db_passkey = profile.salt_passkey.split('|')
		passkey = KDF.PBKDF2(request.password, db_salt.decode('hex')).encode('hex')

		# Passwords don't match, return False
		if passkey != db_passkey:
			return status

		# Update user's status to logged-in
		profile.loggedIn = True
		profile.put()

		# Generate user access token (extra_secret = salt)
		token = self._genToken({'userId': user_id})

		# If we get here, means we suceeded
		status.data = True
		status.accessToken = token
		return status

	@endpoints.method(AccessTokenMsg, BooleanMsg, path='',
		http_method='POST', name='logout')
	def logout(self, request):
		""" Logout """
		status = BooleanMsg()  # return status
		status.data = False  # default to error (False)

		user_id = self._getUserId(request.accessToken)

		# Get Profile from NDB, update login status
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()
		profile.loggedIn = False
		profile.put()

		status.data = True
		return status


	###################################################################
	# Facebook Authentication & Graph API
	###################################################################

	def _getFbUserId(self, token):
		""" Given token, find FB user ID from FB, and return it """
		url = 'https://graph.facebook.com/v%s/me?access_token=%s&fields=id' % (FB_API_VERSION, token)
		try:
			result = urlfetch.Fetch(url, method=1)
		except:
			raise endpoints.BadRequestException('urlfetch error: Get FB user ID')
			return None

		data = json.loads(result.content)
		if 'error' in data:
			raise endpoints.BadRequestException('FB OAuth token error')
			return None

		user_id = 'fb_' + data['id']
		return user_id

	def _postFbNotif(self, fb_user_id, message):
		"""
		Post FB notification with message to user
		"""
		# Get App Access Token, different than User Token
		# https://developers.facebook.com/docs/facebook-login/access-tokens/#apptokens
		url = 'https://graph.facebook.com/v%s/oauth/access_token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (FB_API_VERSION, FB_APP_ID, FB_APP_SECRET)
		try:
			result = urlfetch.Fetch(url, method=1)
		except:
			raise endpoints.BadRequestException('urlfetch error: FB app access token')
			return False

		token = json.loads(result.content)['access_token']

		url = 'https://graph.facebook.com/v%s/%s/notifications?access_token=%s&template=%s&href=login' % (FB_API_VERSION, fb_user_id, token, message)
		try:
			result = urlfetch.Fetch(url, method=2)
		except:
			raise endpoints.BadRequestException('urlfetch error: Unable to POST FB notification')
			return False

		data = json.loads(result.content)
		if 'error' in data:
			raise endpoints.BadRequestException('FB notification error')
			return False

		return True


	@endpoints.method(AccessTokenMsg, StringMsg, path='',
		http_method='POST', name='fbLogin')
	def fbLogin(self, request):
		""" Handle Facebook login """
		status = StringMsg()  # return status message
		status.data = 'error'  # default to error message, unless specified otherwise
		'''
		# Swap short-lived token for long-lived token
		short_token = request.data

		url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
			FB_APP_ID, FB_APP_SECRET, short_token)
		try:
			result = urlfetch.Fetch(url, method=1)
		except:
			print('urlfetch error1')
			return status

		token = result.content.split('&')[0]  # 'access_token=blahblahblah'
		'''
		token = request.accessToken

		# Use token to get user info from API
		url = 'https://graph.facebook.com/v%s/me?access_token=%s&fields=name,id,email' % (FB_API_VERSION, token)
		try:
			result = urlfetch.Fetch(url, method=1)
		except:
			print('urlfetch error')
			return status

		data = json.loads(result.content)

		if 'error' in data:
			print('FB OAuth token error')
			return status

		user_id = 'fb_' + data['id']
		first_name = data['name'].split()[0]
		last_name = data['name'].split()[-1]
		email = data['email']

		# Get existing profile from datastore, or create new one
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If profile already exists, return 'existing_user'
		# Unless, they have empty firstName (maybe they got d/c'ed on profile page)
		if profile:
			# If empty first name, return new_user
			if profile.firstName == '':
				status.data = 'new_user'
				return status

			# If user previously logged-out, update login status in NDB
			if not profile.loggedIn:
				profile.loggedIn = True
				profile.put()

			status.data = 'existing_user'
			return status

		# Else, create new profile and return 'new_user'
		profile = Profile(
			key = profile_key,
			userId = user_id,
			contactEmail = email,
			firstName = first_name,
			lastName = last_name,
			loggedIn = True
		)
		profile.put()

		status.data = 'new_user'
		return status


	###################################################################
	# Profile Objects
	###################################################################

	def _copyProfileToForm(self, prof):
		"""Copy relevant fields from Profile to ProfileMsg."""
		pf = ProfileMsg()
		for field in pf.all_fields():
			if hasattr(prof, field.name):
				setattr(pf, field.name, getattr(prof, field.name))
		pf.check_initialized()
		return pf

	@endpoints.method(AccessTokenMsg, ProfileMsg,
			path='', http_method='POST', name='getProfile')
	def getProfile(self, request):
		"""Return user profile."""
		token = request.accessToken
		user_id = self._getUserId(token)

		# Create new ndb key based on unique user ID (email)
		# Get profile from datastore -- if profile not found, then profile=None
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If profile is empty, something is wrong
		if not profile:
			print('ERROR: User should have initial profile')

		return self._copyProfileToForm(profile)

	@endpoints.method(ProfileMsg, ProfileMsg,
			path='', http_method='POST', name='updateProfile')
	def updateProfile(self, request):
		"""Update user profile."""
		token = request.accessToken
		user_id = self._getUserId(token)

		# Make sure the incoming message is initialized, raise exception if not
		request.check_initialized()

		# Get existing profile from datastore
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# Update profile object from the user's form
		for field in request.all_fields():
			if field.name == 'userId':
				setattr(profile, 'userId', user_id)
			elif field.name != 'accessToken':
				setattr(profile, field.name, getattr(request, field.name))

		# If this is user's first time updating profile, or changing email address (FB user only)
		# then send email verification
		print('wtf dude')  # DEBUG
		if profile.pristine or (profile.contactEmail != request.contactEmail):
			profile.pristine = False
			print('howdy')  # DEBUG
			self._emailVerif(profile)

		# Save updated profile to datastore
		profile.put()

		return self._copyProfileToForm(profile)


	###################################################################
	# Match Objects
	###################################################################

	@ndb.transactional(xg=True)
	def _createMatch(self, request):
		"""Create new Match, update user Profile to add new Match to Profile.
		Returns MatchMsg/request."""
		token = request.accessToken
		user_id = self._getUserId(token)

		# If any field in request is None, then raise exception
		if any([getattr(request, field.name) is None for field in request.all_fields()]):
			raise endpoints.BadRequestException('All input fields required to create a match')

		# Copy MatchMsg/ProtoRPC Message into dict
		data = {field.name: getattr(request, field.name) for field in request.all_fields()}
		del data['accessToken']  # don't need this for match object

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
		token = request.accessToken
		user_id = self._getUserId(token)

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
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()
		profile.matches.append(match_key)
		profile.put()

		# Notify all other players that current user/player has joined the match
		player_name = profile.firstName + ' ' + profile.lastName
		for other_player in match.players:
			if other_player == user_id:
				continue

			if other_player[3:] == 'fb_':
				# FB notification
				fb_user_id = other_player[3:]
				self._postFbNotif(fb_user_id, urlquote(player_name + ' has joined your match'))

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
		token = request.accessToken
		user_id = self._getUserId(token)

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
		match_removed = False
		if len(match.players) == 0:
			match.key.delete()
			match_removed = True
		else:
			match.put()

		# Remove current match key from current user's matches list
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()
		profile.matches.remove(match_key)
		profile.put()

		if not match_removed:
			# Notify all other players that current user/player has joined the match
			player_name = profile.firstName + ' ' + profile.lastName
			for other_player in match.players:
				if other_player[3:] == 'fb_':
					# FB notification
					fb_user_id = other_player[3:]
					self._postFbNotif(fb_user_id, urlquote(player_name + ' has left your match'))

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


	@endpoints.method(AccessTokenMsg, MatchesMsg,
			path='', http_method='POST', name='getMyMatches')
	def getMyMatches(self, request):
		"""Get all confirmed or pending matches for current user."""
		token = request.accessToken
		user_id = self._getUserId(token)

		# Get user Profile based on userId (email)
		profile = ndb.Key(Profile, user_id).get()

		# Create new MatchesMsg message
		matches_msg = MatchesMsg()

		# For each match is user's matches, add the info to match_msg
		for match_key in profile.matches:
			match = ndb.Key(urlsafe=match_key).get()

			self._appendMatchesMsg(match, matches_msg)

		return matches_msg

	@endpoints.method(AccessTokenMsg, MatchesMsg,
			path='', http_method='POST', name='getAvailableMatches')
	def getAvailableMatches(self, request):
		"""
		Get all available matches for current user.
		Search through DB to find partners of similar skill.
		"""
		token = request.accessToken
		user_id = self._getUserId(token)

		# Get user Profile based on userId
		profile = ndb.Key(Profile, user_id).get()

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
