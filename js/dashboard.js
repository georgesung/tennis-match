'use strict';

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (authResult && !authResult.error) {
		gapi.client.tennis.getProfile().
			execute(function (resp) {
				console.log(resp.result.displayName);
				console.log(resp.result.mainEmail);
			});
	} else {
		console.log('auth failed!');
	}
}
