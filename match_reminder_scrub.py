'''
Cron job to send match reminders and delete old matches
'''

from datetime import datetime
from datetime import timedelta
from eastern_tzinfo import Eastern_tzinfo
import json
import os
from django.utils.http import urlquote

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from models import Profile
from models import Match


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