'use strict';

// AngularJS
var app = angular.module('create-account', []);

app.controller('CaCtrl', function() {
	var ca = this;

	ca.submitForm = function() {
		// First, disable all inputs while in process
		$('.container :input, select, button').attr('disabled', true);

		// Read values from form
		var email    = $('#email').val();
		var password = $('#password').val();

		// Obtain reCAPTCHA response
		var recaptcha = grecaptcha.getResponse();

		// Construct message to send to back-end API
		var createAccountMsg = {
			'email':     email,
			'password':  password,
			'recaptcha': recaptcha,
		};

		// Call back-end API
		gapi.client.tennis.createAccount(createAccountMsg).
			execute(function(resp) {
				if (resp.result.data == 'success') {
					// Account creation successful. Give user token and redirect to profile page.
					localStorage.tennisJwt = resp.result.accessToken;
					window.location = '/profile';

				} else if (resp.result.data == 'user_exists') {
					// User already exists, notify and enable the buttons.
					$('#status').text('This email is already registered');
					$('.container :input, select, button').attr('disabled', false);
					grecaptcha.reset();

				} else if (resp.result.data == 'recaptcha_fail') {
					// reCAPTCHA failed, notify and enable the buttons.
					$('#status').text('Please verify you are not a robot');
					$('.container :input, select, button').attr('disabled', false);

				} else {
					console.log('Uknown error...');
					$('.container :input, select, button').attr('disabled', false);
					grecaptcha.reset();
				}
			});
	}
});

// Use Jquery validate plugin to validate form
// Maybe migrate this to AngularJS?
$("#createAccountForm").validate({
	rules: {
		email: {
			required: true,
			email: true
		},
		password: {
			required: true,
			minlength: 6,
			maxlength: 20,
		},
		confPassword: {
			equalTo: "#password",
			minlength: 6,
			maxlength: 20
		}
	},

	messages:{
		email: "A valid email is required.",
		password: "A password between 6-20 characters is required.",
		confPassword: {
			equalTo: "Passwords do not match."
		}
	}
});

// Cancel button redirects to dashboard
$('#cancel').click(function() {
	window.location = '/';
});