'use strict';

// AngularJS
angular.module('dashboard', [])
	.controller('DashboardCtrl', function() {
		var dash = this;
		dash.firstName = '';
		dash.confirmedMatches = [];
		dash.pendingMatches = [];
		dash.availableMatches = [];
	});


// Declare classes
var Match = function(singles, date, time, location, players, confirmed) {
	this.singles = singles;
	this.date = date;
	this.time = time;
	this.location = location;
	this.players = players;
	this.confirmed = confirmed;
};


// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	// Get Angular scope
	var $scope = $('#dashboard').scope();

	if (authResult && !authResult.error) {
		// Get user profile, show personalized greeting
		gapi.client.tennis.getProfile().execute(function(resp) {
			var userId = resp.result.userId;

			// If user has not created a profile, redirect to profile page
			// Else, stay here and update greeting
			if (resp.result.firstName == '' || resp.result.lastName == '') {
				window.location.href = '/profile';
			} else {
				$scope.$apply(function () { $scope.dash.firstName = resp.result.firstName; });
			}
		});

		// Get all matches for current user, populate Confirmed Matches and Pending Matches
		gapi.client.tennis.getMyMatches().execute(function(resp) {
			// The MatchesMsg message is stored in resp.result
			// Go through all matches in the match "list" (see models.py for format)
			var matches = resp.result;
			var num_matches = matches.singles.length;

			var confirmedMatches = [];
			var pendingMatches = [];
			var availableMatches = [];

			for (var i = 0; i < num_matches; i++) {
				var newMatch = new Match(
					matches.singles[i],
					matches.date[i],
					matches.time[i],
					matches.location[i],
					matches.players[i],
					matches.confirmed[i]
				);

				if (newMatch.confirmed) {
					confirmedMatches.push(newMatch);
				} else {
					pendingMatches.push(newMatch);
				}
			}

			// Point to the confirmed/pendingMatches in the controller
			$scope.$apply(function () {
				$scope.dash.confirmedMatches = confirmedMatches;
				$scope.dash.pendingMatches = pendingMatches;
			});
		});

	} else {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}

// On-click handlers
$('#req-button').click(function() {
	window.location.href = '/req_match';
});

$('.conf-match').click(function() {
	window.location.href = '/conf_match';
});

$('.pend-match').click(function() {
	window.location.href = '/pend_match';
});

$('.avail-match').click(function() {
	window.location.href = '/avail_match';
});
