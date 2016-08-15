// Facebook SDK & OAuth
(function(d, s, id){
	var js, fjs = d.getElementsByTagName(s)[0];
	if (d.getElementById(id)) {return;}
	js = d.createElement(s); js.id = id;
	js.src = "//connect.facebook.net/en_US/sdk.js";
	fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));

window.fbAsyncInit = function() {
	FB.init({
		appId      : '1739379949638650',
		cookie     : false, // enable cookies to allow the server to access the session?
		xfbml      : true,  // parse social plugins on this page?
		version    : 'v2.7'
	});

	// Additional intialization code
	// Quick redirect for users not auth'ed
	if (window.location.pathname !== '/login') {
		if (localStorage.tennisJwt === undefined) {
			FB.getLoginStatus(function(response) {
				if (response.status !== 'connected') {
					window.location = '/login';
				}
			});
		}
	}
};

function getAccessTokenGlobal() {
	/* Get valid access token from localStorage or FB. If invalid, redirect to login page. */
	var accessToken = localStorage.tennisJwt;

	if (accessToken === undefined) {
		//tryFb();
		FB.getLoginStatus(function(response) {
			if (response.status === 'connected') {
				// Authenticated
				accessToken = response.authResponse.accessToken;
			} else {
				// Not authenticated, redirect to login page
				window.location = '/login';
			}
		});
	} else {
		// Verify token and user login status with back-end
		gapi.client.tennis.verifyToken({accessToken: accessToken}).execute(function(resp) {
			if (resp.result.data === false) {
				//tryFb();
				FB.getLoginStatus(function(response) {
					if (response.status === 'connected') {
						// Authenticated
						accessToken = response.authResponse.accessToken;
					} else {
						// Not authenticated, redirect to login page
						window.location = '/login';
					}
				});
			}
		});
	}

	return accessToken;
}

// Google OAuth
/*
CLIENT_ID = 'secret';
SCOPES = 'email profile';
*/