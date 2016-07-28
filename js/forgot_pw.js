'use strict';

// Any back-end API functionality must be executed -after- the gapi is loaded
// Set button's on-click listener to call back-end
$('#sendLink').click(function() {
	console.log('hihi');
	var email = $('#email');
	var recaptcha = grecaptcha.getResponse();

	// Disable buttons while back-end API call in progress
	$('.container :input, select, button').attr('disabled', true);

	// Call back-end API
	gapi.client.tennis.forgotPassword({'email': email, 'recaptcha': recaptcha}).
		execute(function(resp) {
			var status = '';

			if (resp.result.data === 'success') {
				status = 'A password reset link has been emailed to you. Please visit the link within 30 minutes.';

			} else if (resp.result.data === 'invalid_email') {
				status = 'This email is not registered';
				$('.container :input, select, button').attr('disabled', false);
				grecaptcha.reset();

			} else if (resp.result.data === 'unverified_email') {
				status = 'Sorry, the email address was never verified, so we cannot send the password reset link. Please contact me@georgesungtennis.com for help.';
				$('.container :input, select, button').attr('disabled', false);
				grecaptcha.reset();

			} else if (resp.result.data == 'recaptcha_fail') {
				status = 'Please verify you are not a robot';
				$('.container :input, select, button').attr('disabled', false);
				grecaptcha.reset();

			} else {
				status = 'An unknown error occured';
				$('.container :input, select, button').attr('disabled', false);
				grecaptcha.reset();
			}

			$('#status').html(status);
		});
});

// Use Jquery validate plugin to validate form
// Maybe migrate this to AngularJS?
$("#forgotPwForm").validate({
	rules: {
		email: {
			required: true,
			email: true
		},
	},

	messages:{
		email: "A valid email is required.",
	}
});