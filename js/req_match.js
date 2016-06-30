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

$('#req-button').click(function() {
	bootbox.dialog({
		message: "FIXME: Are you sure I need this dialog? Too much friction!",
		buttons: {
			yes: {
				label: "Yes",
				className: "btn-primary",
				callback: function() {
					console.log("yes!");
				}
			},
			no: {
				label: "No",
				className: "btn-default",
				callback: function() {
					console.log("no~");
				}
			}
		}
	});});