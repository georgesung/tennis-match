// Code below based on:
// https://developers.google.com/maps/documentation/javascript/examples/places-searchbox

function initAutocomplete() {
	// Find out the location string
	var location = document.getElementById('pac-input').placeholder;

	// Execute Google Places search
	var request = {
		location: {lat: 42.355137, lng: -71.065604},
		radius: '50000',  // 50000 meters ~ 31 miles
		query: location
	};
	service = new google.maps.places.PlacesService(map);
	service.textSearch(request, locSearchCallback);
}

function locSearchCallback(results, status) {
	var map = new google.maps.Map(document.getElementById('map'), {
		center: {lat: 42.355137, lng: -71.065604},
		zoom: 12,
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		mapTypeControl: false,
	});

	if (status == google.maps.places.PlacesServiceStatus.OK) {
		var place = results[0];

		var bounds = new google.maps.LatLngBounds();

		// Create a marker for each place.
		var markers = [];
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
		map.setZoom(12);  // doesn't work
	}
}

// On-click handlers
$('#back-button').click(function() {
	window.location.href = '/dashboard';
});

$('#cancel-button').click(function() {
	bootbox.dialog({
		message: "Are you sure?",
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
	});
});