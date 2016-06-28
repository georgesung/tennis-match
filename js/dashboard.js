'use strict';

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (authResult && !authResult.error) {
		gapi.client.tennis.getProfile().
			execute(function(resp) {
				var userId = resp.result.userId;

				$('#greeting').text('Welcome, ' + userId);
			});
	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}

// On-click handlers
$('#req-button').click(function() {
	window.location.href = '/req_match';
});

$('.conf-match').click(function() {
	window.location.href = '/conf_match';
});

$('.pend-match').click(function() {
	window.location.href = '/pend_match';
});

$('.avail-match').click(function() {
	window.location.href = '/avail_match';
});
