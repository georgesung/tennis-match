'use strict';

$('#update-profile').click(function() {
	console.log('you clik!');

	// FIXME: How do I pass a message from front-end to back-end???
	var profile = {
		'userId': 'aa',
		'mainEmail': 'bb',
		'firstName': 'Brute',
		'lastName': 'Force',
	};

	gapi.client.tennis.updateProfile(profile).
		execute(function(resp) {
			console.log('yay!');
		});
});

// Mandatory (?) Google API stuff?

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (authResult && !authResult.error) {
		gapi.client.tennis.getProfile().
			execute(function(resp) {
				//console.log(resp.result.displayName);
				//console.log(resp.result.mainEmail);

				var userEmail = resp.result.mainEmail;

				console.log('Your email is: ' + userEmail);
			});
	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}
