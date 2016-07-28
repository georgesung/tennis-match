'use strict';

///////////////////////////////////////////////////////
// AngularJS
///////////////////////////////////////////////////////

var app = angular.module('profile', []);

app.controller('ProfCtrl', function() {
	var prof = this;
	prof.accessToken = '';
	prof.fbUser = false;
	prof.fbNotifEn = false;
	prof.emailNotifEn = false;

	prof.submitForm = function(isValid) {
		if (isValid) {
			// First, disable all inputs while profile update is in process
			$('.container :input, select, button').attr('disabled', true);

			// Read values from form
			var contactEmail  = $('#contact-email').val();
			var firstName     = $('#first-name').val();
			var lastName      = $('#last-name').val();
			var gender        = $('#gender').val();
			var ntrp          = parseFloat($('#ntrp').val());
			var fbNotifEn     = $('#fb-notif-en').is(':checked');
			var emailNotifEn  = $('#email-notif-en').is(':checked')

			var profile = {
				'userId':        '',
				'contactEmail':  contactEmail,
				'firstName':     firstName,
				'lastName':      lastName,
				'gender':        gender,
				'ntrp':          ntrp,
				'accessToken':   prof.accessToken,
				'loggedIn':      true,
				'notifications': [fbNotifEn, emailNotifEn]
			};

			// Call back-end API
			gapi.client.tennis.updateProfile(profile).
				execute(function(resp) {
					// If user changed email, notify user
					// Else just redirect to homepage
					if (resp.result.data === 'email_verif') {
						bootbox.dialog({
							closeButton: false,
							message: "New email address, verification email was sent to " + contactEmail,
							buttons: {
								ok: {
									label: "OK",
									className: "btn-default",
									callback: function() {
										window.location = '/';
									}
								}
							}
						});
					} else {
						window.location = '/';
					}
				});
		}
	}
});


///////////////////////////////////////////////////////
// User Authentication
///////////////////////////////////////////////////////

// This function is called after authentication step
function onAuthSuccess(accessToken) {
	// Get Angular scope
	var $scope = $('#profile').scope();

	// If user is authorized, populate fields with user profile info (if logged in)
	// Note userId == 'fb_|ca_' + facebook_id|email
	gapi.client.tennis.getProfile({accessToken: accessToken}).
		execute(function(resp) {
			// If user is logged-out, redirect to login page
			if (!resp.result.loggedIn) {
				window.location = '/login';
			} else {
				$scope.$apply(function () {
					$scope.prof.accessToken = accessToken;
					$scope.prof.email = resp.result.contactEmail;
					$scope.prof.firstName = resp.result.firstName;
					$scope.prof.lastName = resp.result.lastName;
					$scope.prof.gender = resp.result.gender;
					$scope.prof.ntrp = resp.result.ntrp;
					$scope.prof.emailVerified = resp.result.emailVerified;

					$scope.prof.fbUser = resp.result.userId.slice(0,3) === 'fb_';
					$scope.prof.fbNotifEn = (resp.result.userId.slice(0,3) === 'fb_') && resp.result.notifications[0];
					$scope.prof.emailNotifEn = resp.result.notifications[1];
				});

				$('#ntrp').slider().slider('setValue', resp.result.ntrp);
			}
		});
}

// Try FB auth
function tryFb() {
	FB.getLoginStatus(function(response) {
		if (response.status === 'connected') {
			// Authenticated
			var accessToken = response.authResponse.accessToken;

			// Remove custom account token just in case
			localStorage.removeItem('tennisJwt');

			onAuthSuccess(accessToken);
		} else {
			window.location = '/login';
		}
	});
}

// Any back-end API functionality must be executed -after- the gapi is loaded
// Execute authentication steps
function onGapiLoad() {
	// First try custom account authentication
	// If custom auth fails or user logged out of custom account session, try FB auth
	var accessToken = localStorage.tennisJwt;

	if (accessToken === undefined) {
		tryFb();
	} else {
		// Verify token and user login status with back-end
		gapi.client.tennis.verifyToken({accessToken: accessToken}).execute(function(resp) {
			if (resp.result.data === false) {
				tryFb();
			} else {
				// Token is valid and user is logged-in, proceed
				onAuthSuccess(accessToken);
			}
		});
	}
}


///////////////////////////////////////////////////////
// Simple Button onClicks
///////////////////////////////////////////////////////

// Cancel button redirects to dashboard, and discards changes
$('#cancel').click(function() {
	window.location = '/';
});