'use strict';

///////////////////////////////////////////////////////
// Helper classes and functions
///////////////////////////////////////////////////////

var Match = function(singles, date, time, location, players, confirmed, key) {
	this.singles = singles;
	this.date = date;
	this.time = time;
	this.location = location;
	this.players = players;
	this.confirmed = confirmed;
	this.key = key;
};

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


///////////////////////////////////////////////////////
// AngularJS
///////////////////////////////////////////////////////

var app = angular.module('dashboard', ['ngRoute']);

app.config(['$routeProvider', function($routeProvider) {
	$routeProvider
		.when('/',              {templateUrl: '/templates/summary.html', controller: 'SummaryCtrl as summary'})
		.when('/req_match',     {templateUrl: '/templates/req_match.html', controller: 'ReqCtrl as req'})
		.when('/conf_match',    {templateUrl: '/templates/conf_match.html', controller: 'MatchCtrl as match'})
		.when('/pend_match',    {templateUrl: '/templates/pend_match.html', controller: 'MatchCtrl as match'})
		.when('/avail_match',   {templateUrl: '/templates/avail_match.html', controller: 'MatchCtrl as match'})
		.when('/change_pw',     {templateUrl: '/templates/change_pw.html', controller: 'CpwCtrl as cpw'})
		.otherwise({redirectTo:'/'});
}]);

// "Global variables"/services
app.factory('currentMatch', function() {
	var myMatch = new Match(true, '-', '-', '-', '-', false, '-');

	// Boilerplate code
	function set(match) { myMatch = match; }
	function get() { return myMatch; }
	return {
		set: set,
		get: get
	}
});
app.factory('accessToken', function() {
	var accessToken = '';

	// Boilerplate code
	function set(accessTokenIn) { accessToken = accessTokenIn; }
	function get() { return accessToken; }
	return {
		set: set,
		get: get
	}
});

app.controller('SummaryCtrl', function(currentMatch, accessToken) {
	var summary = this;

	summary.firstName = '';
	summary.emailVerified = false;
	summary.fbUser = false;
	summary.confirmedMatches = [];
	summary.pendingMatches = [];
	summary.availableMatches = [];
	summary.pendingMatchesFiltered = [];
	summary.availableMatchesFiltered = [];
	summary.singlesDoubles = 'singles';

	summary.showDashboard = false;

	// Filters matches, only show filtered ones
	summary.filterMatches = function() {
		// Only filter pending and available matches, want to see all confirmed matches
		// BOZO: Only singles/doubles filter for now. Maybe time/location filter later.
		summary.pendingMatchesFiltered = [];
		summary.availableMatchesFiltered = [];
		var singles = (summary.singlesDoubles == 'singles');

		for (var i = 0; i < summary.pendingMatches.length; i++) {
			if (summary.pendingMatches[i].singles == singles) {
				summary.pendingMatchesFiltered.push(summary.pendingMatches[i]);
			}
		}

		for (var i = 0; i < summary.availableMatches.length; i++) {
			if (summary.availableMatches[i].singles == singles) {
				summary.availableMatchesFiltered.push(summary.availableMatches[i]);
			}
		}
	};

	// These functions get called on corresponding button clicks
	summary.showReqMatch = function(match) {
		window.location = '#/req_match';
	};

	summary.showConfMatch = function(match) {
		currentMatch.set(match);
		window.location = '#/conf_match';
	};

	summary.showPendMatch = function(match) {
		currentMatch.set(match);
		window.location = '#/pend_match';
	};

	summary.showAvailMatch = function(match) {
		currentMatch.set(match);
		window.location = '#/avail_match';
	};

	summary.showChangePw = function() {
		window.location = '#/change_pw';
	}

	// Set access token from OAuth provider
	summary.setAccessToken = function(token) {
		accessToken.set(token);
	}

	// Log out user from session
	summary.logout = function() {
		gapi.client.tennis.logout({accessToken: accessToken.get()}).
			execute(function(resp) {
				var status = resp.result.data;

				// If user is logged-out, redirect to login page
				if (status) {
					window.location = '/login';
				} else {
					console.log('Error while logging out');
				}
			});
	}
});

app.controller('ReqCtrl', function(accessToken) {
	var req = this;

	// Regex for form validation
	req.datePattern = '[0-9]{2}/[0-9]{2}/[0-9]{4}';
	req.timePattern = '[0-9]{2}:[0-9]{2}';

	req.submitForm = function(isValid) {
		if (isValid) {
			// First, disable all inputs while match request is in process
			$('.container :input, select, button').attr('disabled', true);

			// Read values from form
			var singlesDoubles = $('#singles-doubles').val();
			var date           = $('#date').val();
			var time           = $('#time').val();
			var location       = $('#pac-input').val();

			// Convert singlesDoubles to boolean
			var singles = singlesDoubles=='singles' ? true : false;

			var match = {
				'singles':   singles,
				'date':      date,
				'time':      time,
				'location':  location,
				'players':   [],     // back-end will set default value
				'confirmed': false,  // ditto
				'ntrp':      0.0,    // ditto
				'accessToken': accessToken.get(),
			};

			// Call back-end API
			gapi.client.tennis.createMatch(match).
				execute(function(resp) {
					if (resp.result.data) {
						bootbox.dialog({
							closeButton: false,
							message: "Match request successful",
							buttons: {
								ok: {
									label: "OK",
									className: "btn-default",
									callback: function() {
										window.location = '/';
									}
								}
							}
						});
					} else {
						$('.container :input, select, button').attr('disabled', false);
						bootbox.dialog({
							closeButton: false,
							message: "Something went wrong, please try again",
							buttons: {
								ok: {
									label: "OK",
									className: "btn-default"
								}
							}
						});

					}
				});
		}
	}
});

app.controller('MatchCtrl', function(currentMatch) {
	var match = this;
	match.currentMatch = currentMatch.get();
});

app.controller('CpwCtrl', function(accessToken) {
	var cpw = this;

	cpw.submitForm = function() {
		var changePasswordMsg = {
			'oldPw': cpw.oldPassword,
			'newPw': cpw.password,
			'accessToken': accessToken.get()
		}

		// Call back-end API
		gapi.client.tennis.changePassword(changePasswordMsg).
			execute(function(resp) {
				var message = '';
				var callback = function() {};

				if (resp.result.data === 'success') {
					message = 'Password change successful, please login again';
					callback = function() { window.location = '/'; };
				} else if (resp.result.data === 'old_pw_wrong') {
					message = 'Incorrect current password';
				} else {
					message = 'Unknown error, please refresh homepage and try again';
				}

				bootbox.dialog({
					closeButton: false,
					message: message,
					buttons: {
						ok: {
							label: "OK",
							className: "btn-default",
							callback: callback
						}
					}
				});
			});
	}
});


///////////////////////////////////////////////////////
// User Authentication
///////////////////////////////////////////////////////

// Show confirmed/pending/available matches for current user (only call after auth'ed)
function showMatches(accessToken) {
	var $scope = $('#dashboard').scope();

	// Get and validate URL query strings
	var matchId = getParameterByName('match_id');
	var validMatchId = matchId !== null && matchId !== '';
	var matchType = getParameterByName('match_type');

	// Get all matches for current user, populate Confirmed Matches and Pending Matches
	gapi.client.tennis.getMyMatches({accessToken: accessToken}).execute(function(resp) {
		//if (resp.result.singles === undefined) { return; }
		// The MatchesMsg message is stored in resp.result
		// Go through all matches in the match "list" (see models.py for format)
		var matches = resp.result;
		var num_matches = (resp.result.singles === undefined) ? 0 : matches.singles.length;

		var confirmedMatches = [];
		var pendingMatches = [];

		for (var i = 0; i < num_matches; i++) {
			var newMatch = new Match(
				matches.singles[i],
				matches.date[i],
				matches.time[i],
				matches.location[i],
				matches.players[i],
				matches.confirmed[i],
				matches.key[i]
			);

			if (newMatch.confirmed) {
				confirmedMatches.push(newMatch);
			} else {
				pendingMatches.push(newMatch);
			}
		}

		// Point to the confirmed/pendingMatches in the controller
		$scope.$apply(function () {
			$scope.summary.confirmedMatches = confirmedMatches;
			$scope.summary.pendingMatches = pendingMatches;

			$scope.summary.filterMatches();
		});

		// Show one particular match
		if (validMatchId && matchType === 'conf_pend') {
			// Search for match in conf/pend match lists
			var match_found = false;

			for (var i = 0; i < confirmedMatches.length; i++) {
				var match = confirmedMatches[i];
				if (matchId === match.key) {
					match_found = true;

					$scope.$apply(function () {
						$scope.summary.showConfMatch(match);
					});
				}
			}
			for (var i = 0; i < pendingMatches.length; i++) {
				var match = pendingMatches[i];
				if (matchId === match.key) {
					match_found = true;

					$scope.$apply(function () {
						$scope.summary.showPendMatch(match);
					});
				}
			}

			if (!match_found) {
				bootbox.dialog({
					closeButton: false,
					message: 'Sorry, this match is no longer available',
					buttons: {
						ok: {
							label: "OK",
							className: "btn-default"
						}
					}
				});
			}
		}
	});

	// Query all available matches for current user, populate Available Matches
	gapi.client.tennis.getAvailableMatches({accessToken: accessToken}).execute(function(resp) {
		//if (resp.result.singles === undefined) { return; }

		// The MatchesMsg message is stored in resp.result
		// Go through all matches in the match "list" (see models.py for format)
		var matches = resp.result;
		var num_matches = (resp.result.singles === undefined) ? 0 : matches.singles.length;

		var availableMatches = [];

		for (var i = 0; i < num_matches; i++) {
			var newMatch = new Match(
				matches.singles[i],
				matches.date[i],
				matches.time[i],
				matches.location[i],
				matches.players[i],
				matches.confirmed[i],
				matches.key[i]
			);

			availableMatches.push(newMatch);
		}

		// Point to the availableMatches in the controller
		$scope.$apply(function () {
			$scope.summary.availableMatches = availableMatches;

			$scope.summary.filterMatches();
		});

		// Show one particular match
		if (validMatchId && matchType === 'avail') {
			// Search for match in avail match list
			var match_found = false;

			for (var i = 0; i < availableMatches.length; i++) {
				var match = availableMatches[i];
				if (matchId === match.key) {
					match_found = true;
					$scope.$apply(function () {
						$scope.summary.showAvailMatch(match);
					});
				}
			}

			if (!match_found) {
				bootbox.dialog({
					closeButton: false,
					message: 'Sorry, this match is no longer available',
					buttons: {
						ok: {
							label: "OK",
							className: "btn-default"
						}
					}
				});
			}
		}
	});
}

// Update dashboard front-end with data from back-end, after authentication is complete
// This function is called after authentication step
function onAuthSuccess(accessToken) {
	// Get Angular scope
	var $scope = $('#dashboard').scope();

	// Request match controller (ReqCtrl) needs the accessToken,
	// since it makes back-end API call to request match for current user
	$scope.$apply(function () { $scope.summary.setAccessToken(accessToken); });

	var profile_valid = false;

	// Get Profile, update greeting on summary (if logged in)
	gapi.client.tennis.getProfile({accessToken: accessToken}).
		execute(function(resp) {
			// If user is logged-out, redirect to login page
			// Else if user has incomplete profile, redirect to profile page
			// Else, update greeting
			if (!resp.result.loggedIn) {
				window.location = '/login';
			} else if (resp.result.firstName == '' || resp.result.gender == '') {
				window.location = '/profile';
			} else {
				// Show the dashboard, update greeting
				$scope.$apply(function () {
					$scope.summary.firstName = resp.result.firstName;
					$scope.summary.emailVerified = resp.result.emailVerified;
					$scope.summary.fbUser = resp.result.userId.slice(0,3) === 'fb_';
					$scope.summary.showDashboard = true;
				});

				// Get and show match info
				showMatches(accessToken);
			}
		});
}

// Try FB auth
function tryFb() {
	FB.getLoginStatus(function(response) {
		if (response.status === 'connected') {
			// Authenticated
			var accessToken = response.authResponse.accessToken;

			// Remove custom account token just in case
			localStorage.removeItem('tennisJwt');

			onAuthSuccess(accessToken);
		} else {
			window.location = '/login';
		}
	});
}

// Any back-end API functionality must be executed -after- the gapi is loaded
// Execute authentication steps
function onGapiLoad() {
	// First try custom account authentication
	// If custom auth fails or user logged out of custom account session, try FB auth
	var accessToken = localStorage.tennisJwt;

	if (accessToken === undefined) {
		tryFb();
	} else {
		// Verify token and user login status with back-end
		gapi.client.tennis.verifyToken({accessToken: accessToken}).execute(function(resp) {
			if (resp.result.data === false) {
				tryFb();
			} else {
				// Token is valid and user is logged-in, proceed
				onAuthSuccess(accessToken);
			}
		});
	}
}
