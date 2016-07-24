'use strict';

// AngularJS
var app = angular.module('profile', []);

app.controller('ProfCtrl', function() {
	var prof = this;
	prof.accessToken = '';

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

			var profile = {
				'userId':        '',
				'contactEmail':  contactEmail,
				'firstName':     firstName,
				'lastName':      lastName,
				'gender':        gender,
				'ntrp':          ntrp,
				'accessToken':   prof.accessToken,
				'loggedIn':      true,
			};

			// Call back-end API
			gapi.client.tennis.updateProfile(profile).
				execute(function(resp) {
					window.location = '/';
				});
		}
	}
});


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
				});

				$('#ntrp').slider().slider('setValue', resp.result.ntrp);
			}
		});
}


// Any back-end API functionality must be executed -after- the gapi is loaded
// Execute authentication steps
function onGapiLoad() {
	// First try Facebook authentication
	FB.getLoginStatus(function(response) {
		if (response.status === 'connected') {
			// Authenticated
			var accessToken = response.authResponse.accessToken;

			onAuthSuccess(accessToken);
		} else {
			// Not authenticated with FB, check if auth'ed with custom account
			// If not, redirect to login page
			var accessToken = localStorage.tennisJwt;

			if (accessToken === undefined) {
				window.location = '/login';
			} else {
				// Verify token with back-end
				gapi.client.tennis.verifyToken({accessToken: accessToken}).execute(function(resp) {
					if (resp.result.data === false) {
						window.location = '/login';
					} else {
						// Token is valid, proceed
						onAuthSuccess(accessToken);
					}
				});
			}
		}
	});
}


// Cancel button redirects to dashboard, and discards changes
$('#cancel').click(function() {
	window.location = '/';
});