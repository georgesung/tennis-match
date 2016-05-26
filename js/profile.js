'use strict';

// Note userId == email

$('#update-profile').click(function() {
	var userId = $('#email-address').val();
	var firstName = $('#first-name').val();
	var lastName = $('#last-name').val();

	var profile = {
		'userId': userId,
		'firstName': firstName,
		'lastName': lastName,
	};

	//gapi.client.tennis.updateProfile(profile).execute();
	gapi.client.tennis.updateProfile(profile).
		execute(function(resp) {
			console.log('FIXME TODO: Please implement redirect');
		});
});

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (authResult && !authResult.error) {
		// If user is authorized, populate fields with user profile info
		gapi.client.tennis.getProfile().
			execute(function(resp) {
				$('#email-address').val(resp.result.userId);
				$('#first-name').val(resp.result.firstName);
				$('#last-name').val(resp.result.lastName);
			});
	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}
