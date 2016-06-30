'use strict';

// Google sign-in
function onSuccess(googleUser) {
	//console.log('Logged in as: ' + googleUser.getBasicProfile().getName());
	window.location.href = '/dashboard';
}
function onFailure(error) {
	//console.log(error);
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