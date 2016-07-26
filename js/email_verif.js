'use strict';

// Get query strings
// http://stackoverflow.com/a/901144
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

// Any back-end API functionality must be executed -after- the gapi is loaded
function onGapiLoad() {
	// Get token value from the URL
	var token = getParameterByName('token');
	console.log('hi');

	// Call back-end API to verify email token
	gapi.client.tennis.verifyEmailToken({'accessToken': token}).
		execute(function(resp) {
			var status = '';
			console.log(resp.result.data);
			if (resp.result.data === 'error') {
				// Email verif fail
				console.log('really?');

				status = 'Invalid link. Perhaps you changed your email in your profile?'

				$('#status').html(status);
			} else {
				// Email verif successful
				status = 'You have successfully verified <b>' + resp.result.data +
					'</b><br>You can close this window, or <a href="/">visit the homepage</a></div>';

				$('#status').html(status);
			}
		});
}