// Facebook SDK & OAuth
window.fbAsyncInit = function() {
	FB.init({
		appId      : '1739379949638650',
		cookie     : false, // enable cookies to allow the server to access the session?
		xfbml      : true,  // parse social plugins on this page?
		version    : 'v2.7'
	});
};

(function(d, s, id){
	var js, fjs = d.getElementsByTagName(s)[0];
	if (d.getElementById(id)) {return;}
	js = d.createElement(s); js.id = id;
	js.src = "//connect.facebook.net/en_US/sdk.js";
	fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

function getAccessTokenGlobal() {
	/* Get access token from FB */
	var accessToken = '';

	// Facebook authentication
	FB.getLoginStatus(function(response) {
		if (response.status === 'connected') {
			// Authenticated
			accessToken = response.authResponse.accessToken;
		} else {
			// Not authenticated, redirect to login page
			window.location = '/login';
		}
	});

	return accessToken;
}

// Google OAuth
/*
CLIENT_ID = 'secret';
SCOPES = 'email profile';
*/