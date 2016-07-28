'use strict';

// Use Jquery validate plugin to validate form
// Maybe migrate this to AngularJS?
$("#changePwForm").validate({
	rules: {
		oldPassword: {
			required: true
		},
		password: {
			required: true,
			minlength: 6,
			maxlength: 20
		},
		confPassword: {
			equalTo: "#password",
			minlength: 6,
			maxlength: 20
		}
	},

	messages:{
		oldPassword: "Please enter your current password.",
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