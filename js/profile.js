'use strict';

// AngularJS
var app = angular.module('profile', []);

app.controller('ProfCtrl', function() {
	var prof = this;

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
				'userId':        'read-from-backend',
				'contactEmail':  contactEmail,
				'firstName':     firstName,
				'lastName':      lastName,
				'gender':        gender,
				'ntrp':          ntrp,
			};

			// Call back-end API
			gapi.client.tennis.updateProfile(profile).
				execute(function(resp) {
					window.location.href = '/dashboard';
				});
		}
	}
});


// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (authResult && !authResult.error) {
		// If user is authorized, populate fields with user profile info
		// Note userId == accountEmail
		gapi.client.tennis.getProfile().
			execute(function(resp) {
				// Angular scope
				var $scope = $('#profile').scope();

				$scope.$apply(function () {
					$scope.prof.userId = resp.result.userId;
					$scope.prof.email = resp.result.contactEmail;
					$scope.prof.firstName = resp.result.firstName;
					$scope.prof.lastName = resp.result.lastName;
					$scope.prof.gender = resp.result.gender;
					$scope.prof.ntrp = resp.result.ntrp;
				});

				$('#ntrp').slider().slider('setValue', resp.result.ntrp);
			});
	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}

// Cancel button redirects to dashboard, and discards changes
$('#cancel').click(function() {
	window.location.href = '/dashboard';
});