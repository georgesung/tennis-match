////////////////////////////////////////////////////////////////////
// Get match messages
////////////////////////////////////////////////////////////////////
function getMatchMsgs() {
	var $scope = $('#dashboard').scope();
	var accessToken = getAccessTokenGlobal();  // OAuth access token

	// Get match key from front-end, get match messages from back-end
	var matchKey = {data: $scope.match.currentMatch.key, accessToken: accessToken};

	gapi.client.tennis.getMatchMsgs(matchKey).execute(function(resp) {

		if (resp.result.data === undefined) {console.log('error from back-end');}
		var msgs = resp.result.data;

		// Text string to display all messages
		var msgs_string = '';

		for (var i = 0; i < msgs.length; i++) {
			// Parse the message (player_name|message), deal w/ extra pipes in actual msg
			var [player_name, msg] = msgs[i].split(/\|(.+)?/);

			// Build up the messages string to display
			msgs_string += player_name + ': ' + msg;
			if (i < msgs.length - 1) {
				msgs_string += '\n';
			}
		}

		// Show the messages
		$('#match-msgs').text(msgs_string);
	});
}

// Run the above when page first loads
var $scope = $('#dashboard').scope();
$scope.$on('$viewContentLoaded', function(event) {
	getMatchMsgs();
});
