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
from settings import EMAIL_VERIF_SECRET
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

	def _sendEmail(self, user_id, message, message_type):
		"""
		Send generic email to user, given content message, and message type (corresponds to SparkPost template ID)
		"""
		# Get profile of user_id
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If user disabled email notifications or email is unverified, return
		if not profile.notifications[1] or not profile.emailVerified:
			return False

		# Create SparkPost request to send notification email
		payload = {
			'recipients': [{
				'address': {
					'email': profile.contactEmail,
					'name': profile.firstName + ' ' + profile.lastName,
				},
				'substitution_data': {
					'first_name': profile.firstName,
					'message':    message,
				},
			}],
			'content': {
				'template_id': message_type,
			},
		}
		payload_json = json.dumps(payload)
		headers = {
			'Authorization': SPARKPOST_SECRET,
			'Content-Type': 'application/json',
		}

		# POST to SparkPost API
		url = 'https://api.sparkpost.com/api/v1/transmissions?num_rcpt_errors=3'
		try:
			result = urlfetch.Fetch(url, headers=headers, payload=payload_json, method=2)
		except:
			raise endpoints.BadRequestException('urlfetch error: Unable to POST to SparkPost')
			return False
		data = json.loads(result.content)

		# Determine status of email verification from SparkPost, return True/False
		if 'errors' in data:
			return False
		if data['results']['total_accepted_recipients'] != 1:
			return False

		return True

	def _emailVerif(self, profile):
		""" Send verification email, given reference to Profile object. Return success True/False. """
		# Generate JWT w/ payload of userId and email, secret is EMAIL_VERIF_SECRET
		token = jwt.encode(
			{'userId': profile.userId, 'contactEmail': profile.contactEmail},
			EMAIL_VERIF_SECRET,
			algorithm='HS256'
		)

		# Create SparkPost request to send verification email
		payload = {
			'recipients': [{
				'address': {
					'email': profile.contactEmail,
					'name': profile.firstName + ' ' + profile.lastName,
				},
				'substitution_data': {
					'first_name': profile.firstName,
					'token':      token,
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

		# POST to SparkPost API
		url = 'https://api.sparkpost.com/api/v1/transmissions?num_rcpt_errors=3'
		try:
			result = urlfetch.Fetch(url, headers=headers, payload=payload_json, method=2)
		except:
			raise endpoints.BadRequestException('urlfetch error: Unable to POST to SparkPost')
			return False
		data = json.loads(result.content)

		# Determine status of email verification from SparkPost, return True/False
		if 'errors' in data:
			return False
		if data['results']['total_accepted_recipients'] != 1:
			return False

		return True


	@endpoints.method(AccessTokenMsg, StringMsg, path='',
		http_method='POST', name='verifyEmailToken')
	def verifyEmailToken(self, request):
		""" Verify email token, to verify email address. Return email address string or 'error' """
		status = StringMsg()  # return status
		status.data = 'error'  # default to error

		# Decode the JWT token
		try:
			payload = jwt.decode(request.accessToken, EMAIL_VERIF_SECRET, algorithm='HS256')
		except:
			return status

		# If valid JWT token, extract the info and update DB if applicable
		user_id = payload['userId']
		email = payload['contactEmail']

		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# If user changed email and clicked on old email verif link, this request is invalid
		if profile.contactEmail != email:
			return status

		# If we get here then email is verified. Update DB and return successful status
		profile.emailVerified = True
		profile.put()

		status.data = email
		return status


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
		""" Verify validity of custom account token, check if user is logged in. Return True/False. """
		status = BooleanMsg()  # return status
		status.data = False  # default to invalid (False)

		ca_payload = self._decodeToken(request.accessToken)
		if ca_payload is not None:
			if 'userId' in ca_payload:
				# Check if user is logged in
				user_id = ca_payload['userId']
				profile_key = ndb.Key(Profile, user_id)
				profile = profile_key.get()
				if profile is not None:
					status.data = profile.loggedIn

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
			emailVerified = False,
			notifications = [False, True]
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

	def _postFbNotif(self, user_id, message, href):
		"""
		Post FB notification with message to user
		"""
		# Get profile of user_id
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		# Only post FB notif if FB user and user enabled FB notifs
		if not (user_id[:3] == 'fb_' and profile.notifications[0]):
			return False

		fb_user_id = user_id[3:]

		# Get App Access Token, different than User Token
		# https://developers.facebook.com/docs/facebook-login/access-tokens/#apptokens
		url = 'https://graph.facebook.com/v%s/oauth/access_token?grant_type=client_credentials&client_id=%s&client_secret=%s' % (FB_API_VERSION, FB_APP_ID, FB_APP_SECRET)
		try:
			result = urlfetch.Fetch(url, method=1)
		except:
			raise endpoints.BadRequestException('urlfetch error: FB app access token')
			return False

		token = json.loads(result.content)['access_token']

		url = 'https://graph.facebook.com/v%s/%s/notifications?access_token=%s&template=%s&href=%s' % (FB_API_VERSION, fb_user_id, token, message, href)
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
			raise endpoints.BadRequestException('urlfetch error')
			return status

		data = json.loads(result.content)

		if 'error' in data:
			raise endpoints.BadRequestException('FB OAuth token error')
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
			loggedIn = True,
			emailVerified = False,
			notifications = [True, False]
		).put()

		status.data = 'new_user'
		return status


	###################################################################
	# Profile Objects
	###################################################################

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

		# If profile does not exist, return empty ProfileMsg
		if not profile:
			return ProfileMsg()

		# Else, copy profile to ProfileForm, and return it
		pf = ProfileMsg()
		for field in pf.all_fields():
			if hasattr(profile, field.name):
				setattr(pf, field.name, getattr(profile, field.name))
		pf.check_initialized()
		return pf

	@endpoints.method(ProfileMsg, StringMsg,
			path='', http_method='POST', name='updateProfile')
	def updateProfile(self, request):
		"""Update user profile."""
		status = StringMsg()
		status.data = 'normal'

		token = request.accessToken
		user_id = self._getUserId(token)

		# Make sure the incoming message is initialized, raise exception if not
		request.check_initialized()

		# Get existing profile from datastore
		profile_key = ndb.Key(Profile, user_id)
		profile = profile_key.get()

		email_change = profile.contactEmail != request.contactEmail

		# Update profile object from the user's form
		for field in request.all_fields():
			if field.name == 'userId':
				setattr(profile, 'userId', user_id)
			elif field.name != 'accessToken':
				setattr(profile, field.name, getattr(request, field.name))

		# If this is user's first time updating profile, or changing email address (FB user only)
		# then send email verification
		if profile.pristine or email_change:
			profile.pristine = False
			self._emailVerif(profile)

			status.data = 'email_verif'

		# Save updated profile to datastore
		profile.put()

		return status


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

			match_url = '?match_id=' + match_key
			email_message = '%s has <b>joined</b> your match. To view your match, <a href="http://www.georgesungtennis.com/%s">click here</a>.' % (player_name, match_url)

			# Try FB and email notifications
			# The functions themselves will test if FB user and/or if they enabled the notification
			self._postFbNotif(other_player, urlquote(player_name + ' has joined your match'), match_url)
			self._sendEmail(other_player, email_message, 'notification')

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
			# Notify all other players that current user/player has left the match
			player_name = profile.firstName + ' ' + profile.lastName
			for other_player in match.players:

				match_url = '?match_id=' + match_key
				email_message = '%s has <b>left</b> your match. To view your match, <a href="http://www.georgesungtennis.com/%s">click here</a>.' % (player_name, match_url)

				# Try FB and email notifications
				# The functions themselves will test if FB user and/or if they enabled the notification
				self._postFbNotif(other_player, urlquote(player_name + ' has left your match'), match_url)
				self._sendEmail(other_player, email_message, 'notification')

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

			# Ignore matches that are full
			if (match.singles and len(match.players) == 2) or (not match.singles and len(match.players) == 4):
				continue

			self._appendMatchesMsg(match, matches_msg)

		return matches_msg


# registers API
api = endpoints.api_server([TennisApi])
