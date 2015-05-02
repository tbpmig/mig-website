var map;
var marker;
var infowindow;
function initialize() {
    var mapOptions = {
        center: { lat: 42.36, lng: -83.7},
        zoom: 10
    };
    map = new google.maps.Map(document.getElementById('map-canvas'),
        mapOptions);
    google.maps.event.addListener(map, 'click', function(event) {
        addMarker(event.latLng);
        console.log(event.latLng);
    });
}
google.maps.event.addDomListener(window, 'load', initialize);

// Add a marker to the map
function addMarker(location) {
    if( marker) {
        marker.setMap(null);
        infowindow.setMap(null);
    }
    marker = new google.maps.Marker({
        position: location,
        map: map,
        title: 'Mike Hand'
    });
    infowindow = new google.maps.InfoWindow({
        content: marker.title
    });
    infowindow.open(marker.get('map'), marker);
    google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(marker.get('map'), marker);
    });
}