'use strict';

// Any Google API functionality must be executed -after- the gapi is loaded, thus it's placed in a callback
function onGapiLoad() {
	// Check Google OAuth
	gapi.auth.authorize({client_id: CLIENT_ID, scope: SCOPES, immediate: true}, handleAuthResult);
}

function handleAuthResult(authResult) {
	if (!(authResult && !authResult.error)) {
		// If user is not authorized, redirect to login page
		window.location = '/login';
	}
}

// Code for Google Maps API and Google Places Search
// Code below based on:
// https://developers.google.com/maps/documentation/javascript/examples/places-searchbox
function initAutocomplete() {
	var map = new google.maps.Map(document.getElementById('map'), {
		center: {lat: 42.355137, lng: -71.065604},
		zoom: 12,
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		mapTypeControl: false,
	});

	// Create the search box and link it to the UI element.
	var input = document.getElementById('pac-input');
	var searchBox = new google.maps.places.SearchBox(input);

	// Bias the SearchBox results towards current map's viewport.
	map.addListener('bounds_changed', function() {
		searchBox.setBounds(map.getBounds());
	});

	var markers = [];
	// Listen for the event fired when the user selects a prediction and retrieve
	// more details for that place.
	searchBox.addListener('places_changed', function() {
		var places = searchBox.getPlaces();

		if (places.length == 0) {
			return;
		}

		// Clear out the old markers.
		markers.forEach(function(marker) {
			marker.setMap(null);
		});
		markers = [];

		// Only get location of first place
		var bounds = new google.maps.LatLngBounds();
		var place = places[0];

		// Create a marker for each place.
		markers.push(new google.maps.Marker({
			map: map,
			title: place.name,
			position: place.geometry.location
		}));

		if (place.geometry.viewport) {
			// Only geocodes have viewport.
			bounds.union(place.geometry.viewport);
		} else {
			bounds.extend(place.geometry.location);
		}

		map.fitBounds(bounds);
		map.setZoom(15);
	});
}

// On-click handlers
$('#back-button').click(function() {
	window.location.href = '/dashboard';
});

// Validate the form, set up form submit handler (function called when submit-type button is pressed)
$('#req-match-form').validate({
	rules: {
		singles:  'required',
		date:     'required',
		time:     'required',
		location: 'required'
	},
	messages: {
		singles:  'Please choose singles/doubles',
		date:     'Please enter date',
		time:     'Please enter time',
		location: 'Please enter location'
	},
	submitHandler: submitHandler,
});

function submitHandler() {
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
	};

	// Call back-end API
	gapi.client.tennis.createMatch(match).
		execute(function(resp) {
			bootbox.dialog({
				closeButton: false,
				message: "Match request successful",
				buttons: {
					ok: {
						label: "OK",
						className: "btn-default",
						callback: function() {
							window.location.href = '/dashboard';
						}
					}
				}
			});
		});
}