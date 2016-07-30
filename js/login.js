'use strict';

// AngularJS
var app = angular.module('login', []);

app.controller('LoginCtrl', function() {
	var lgn = this;

	lgn.submitForm = function() {
		// First, disable all inputs while login is in process
		$('.container :input, select, button').attr('disabled', true);

		// Read values from form
		var email    = $('#email').val();
		var password = $('#password').val();

		var recaptcha = grecaptcha.getResponse();

		var passwordMsg = {
			'email':    email,
			'password': password,
			'recaptcha': recaptcha,
		};

		// Call back-end API
		gapi.client.tennis.login(passwordMsg).
			execute(function(resp) {
				if (resp.result.data == 'error') {
					// Login failed, let user know
					$('#login-status').text('Email/password does not match');
					$('.container :input, select, button').attr('disabled', false);
					grecaptcha.reset();

				} else if (resp.result.data === 'recaptcha_fail') {
					$('#login-status').text('Please verify you are not a robot');
					$('.container :input, select, button').attr('disabled', false);
					grecaptcha.reset();

				} else {
					// Login successful, give user token and redir to dashboard
					try {
						localStorage.tennisJwt = resp.result.accessToken;
						window.location = '/';
					} catch (e) {
						alert('Your web browser does not support storing settings locally. In Safari, the most common cause of this is using "Private Browsing Mode". The user account sign-in process will not work in this case, sorry.')
					}
				}
			});
	}
});


// This is called with the results from from FB.getLoginStatus().
function statusChangeCallback(response) {
	// The response object is returned with a status field that lets the
	// app know the current login status of the person.
	// Full docs on the response object can be found in the documentation
	// for FB.getLoginStatus().
	if (response.status === 'connected') {
		// Logged into your app and Facebook.
		var accessToken = response.authResponse.accessToken;

		// Remove custom account token just in case
		localStorage.removeItem('tennisJwt');

		// Call back-end API
		gapi.client.tennis.fbLogin({accessToken: accessToken}).execute(function(resp) {
			var status = resp.result.data

			// If existing_user, redirect to dashboard
			// Else (new_user), redirect to profile page to update his/her info
			if (status == 'existing_user') {
				window.location = '/';
			} else {
				window.location = '/profile';
			}
		});
	} else if (response.status === 'not_authorized') {
		// The person is logged into Facebook, but not your app.
		document.getElementById('status').innerHTML = 'Please log into this app.';
	} else {
		// The person is not logged into Facebook, so we're not sure if
		// they are logged into this app or not.
		document.getElementById('status').innerHTML = 'Please log into Facebook.';
	}
}

// This function is called when someone finishes with the Login
// Button.  See the onlogin handler attached to it in the sample
// code below.
function fbCheckLoginState() {
	FB.getLoginStatus(function(response) {
		statusChangeCallback(response);
	});
}

/*
// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, null);
	console.log('I dont thinkg you need this');
}

function handleAuthResult(authResult) {
	// If user has already signed-in, redirect to dashboard
	if (authResult && !authResult.error) {
		//window.location = '/';
		console.log('hello');
	}
}

// Google sign-in
function onSuccess(googleUser) {
	window.location = '/';
}
function onFailure(error) {
	console.log('Google sign-in error!');
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
*/