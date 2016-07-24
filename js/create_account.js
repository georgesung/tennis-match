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

		var passwordMsg = {
			'email':    email,
			'password': password,
		};

		// Call back-end API
		gapi.client.tennis.createAccount(passwordMsg).
			execute(function(resp) {
				if (resp.result.data == 'success') {
					console.log('Account creation successful. Give user token and redir to profile page.');
					console.log(resp.result);
					localStorage.jwt = resp.result.accessToken;
				} else if (resp.result.data == 'user_exists') {
					console.log('User already exists, notify and enable the buttons.');
					$('.container :input, select, button').attr('disabled', false);
				} else {
					console.log('Uknown error...');
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