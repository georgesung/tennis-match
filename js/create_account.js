'use strict';

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