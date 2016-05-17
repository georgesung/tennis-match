Under construction! Here's some info:

Google App Engine:

Run local GAE server:
dev_appserver.py ./

Then to go:
http://localhost:8080

To deploy to tennismatch-1314.appspot.com:
appcfg.py -A tennismatch-1314 -V <v123> update ./

To do FB/Google/blah login, use Google Identity Toolkit with GAE, it's a bit complicated:
https://developers.google.com/identity/toolkit/web/quickstart/python#step_1_configure_the_google_identity_toolkit_api
http://stackoverflow.com/questions/31082344/is-google-identity-toolkit-v3-compatible-with-gae-python-sandbox
