'use strict';

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
				$('#account-email').val(resp.result.userId);
				$('#contact-email').val(resp.result.contactEmail);
				$('#first-name').val(resp.result.firstName);
				$('#last-name').val(resp.result.lastName);
				$('#gender').val(resp.result.gender);
				$('#ntrp-rating').slider().slider('setValue', resp.result.ntrpRating);
			});
	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}

// Validate the form, set up form submit handler (function called when submit-type button is pressed)
$('#profile-form').validate({
	rules: {
		firstName: 'required',
		lastName:  'required',
		email: {
			required: true,
			email: true
		}
	},
	messages: {
		firstName: 'Please enter your first name',
		lastName:  'Please enter your last name',
		email:     'Please enter a valid email address'
	},
	submitHandler: submitHandler,
});

function submitHandler() {
	// Read values from form
	var contactEmail  = $('#contact-email').val();
	var firstName     = $('#first-name').val();
	var lastName      = $('#last-name').val();
	var gender        = $('#gender').val();
	var ntrpRating    = parseFloat($('#ntrp-rating').val());

	var profile = {
		'userId':        'read-from-backend',
		'contactEmail':  contactEmail,
		'firstName':     firstName,
		'lastName':      lastName,
		'gender':        gender,
		'ntrpRating':    ntrpRating,
	};

	// Call back-end API
	gapi.client.tennis.updateProfile(profile).
		execute(function(resp) {
			window.location.href = '/dashboard';
		});
}

// Cancel button redirects to dashboard, and discards changes
$('#cancel').click(function() {
	window.location.href = '/dashboard';
});