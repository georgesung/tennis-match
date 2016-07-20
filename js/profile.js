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
					window.location = '/dashboard';
				});
		}
	}
});


// Any back-end API functionality must be executed -after- the gapi is loaded
function onGapiLoad() {
	// Facebook authentication
	FB.getLoginStatus(function(response) {
		if (response.status === 'connected') {
			// Authenticated
			var accessToken = response.authResponse.accessToken;

			// If user is authorized, populate fields with user profile info (if logged in)
			// Note userId == 'fb_' + facebook_id
			gapi.client.tennis.getProfile({accessToken: accessToken}).
				execute(function(resp) {
					// If user is logged-out, redirect to login page
					if (!resp.result.loggedIn) {
						window.location = '/login';
					}

					// Angular scope
					var $scope = $('#profile').scope();

					$scope.$apply(function () {
						$scope.prof.accessToken = accessToken;
						$scope.prof.email = resp.result.contactEmail;
						$scope.prof.firstName = resp.result.firstName;
						$scope.prof.lastName = resp.result.lastName;
						$scope.prof.gender = resp.result.gender;
						$scope.prof.ntrp = resp.result.ntrp;
					});

					$('#ntrp').slider().slider('setValue', resp.result.ntrp);
				});
		} else {
			// Not authenticated, redirect to login page
			window.location = '/login';
		}
	});
}

// Cancel button redirects to dashboard, and discards changes
$('#cancel').click(function() {
	window.location.href = '/dashboard';
});