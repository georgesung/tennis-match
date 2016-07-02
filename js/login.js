'use strict';

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	// If user has already signed-in, redirect to dashboard
	if (authResult && !authResult.error) {
		//window.location.href = '/dashboard';
		console.log('hello');
	}
}

// Google sign-in
function onSuccess(googleUser) {
	window.location.href = '/dashboard';
}
function onFailure(error) {
	alert('Sign-in error!');
}
function renderButton() {
	gapi.signin2.render('my-signin2', {
		'scope': 'email profile',
		'width': 240,
		'height': 50,
		'longtitle': true,
		'theme': 'dark',
		'onsuccess': onSuccess,
		'onfailure': onFailure
	});
}