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

// AngularJS
var app = angular.module('reset-pw', []);

app.controller('ResetPwCtrl', function() {
	var rpw = this;

	rpw.submitForm = function() {
		// Get token value from the URL
		var token = getParameterByName('token');

		// Get user password input
		var password = $('#password').val();

		// Disable buttons while back-end API call in progress
		$('.container :input, select, button').attr('disabled', true);

		// Call back-end API
		gapi.client.tennis.resetPassword({'data': password, 'accessToken': token}).
			execute(function(resp) {
				var status = '';

				if (resp.result.data === 'success') {
					status = 'You have successfully reset your password, please <a href="/login">login</a> with your new password';

				} else if (resp.result.data === 'invalid_token') {
					status = 'Your password reset link is invalid/expired, please visit <a href="/forgot_password">forgot password</a> to generate a new one';
					$('.container :input, select, button').attr('disabled', false);

				} else {
					status = 'An unknown error has occured';
					$('.container :input, select, button').attr('disabled', false);
				}

				$('#status').html(status);
			});
	};
});

// Use Jquery validate plugin to validate form
// Maybe migrate this to AngularJS?
$("#resetPwForm").validate({
	rules: {
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
		password: "A password between 6-20 characters is required.",
		confPassword: {
			equalTo: "Passwords do not match."
		}
	}
});