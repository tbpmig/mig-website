from decimal import Decimal,InvalidOperation
from math import sin, cos, atan2, radians, sqrt, degrees

from django.core.exceptions import ValidationError
from django.db import models
from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.six import with_metaclass
from django.utils.translation import ugettext as _

class GeoLocation(object):
    """ A location represented by a latitude and longitude pair. """
    
    @classmethod
    def from_string(cls,string):
        if string is None:
            return GeoLocation(None,None)
        ll = string.split(',')
        if len(ll) != 2:
            raise ValidationError(_('Location must be a latitude/longitude pair.'))
        try:
            latitude = Decimal(ll[0].strip())
            longitude = Decimal(ll[1].strip())
            return GeoLocation(latitude,longitude)
        except InvalidOperation:
            raise ValidationError(_('Could not convert entries to decimal.'))
    def __init__(self,lat,long):
        self.latitude = lat
        self.longitude = long
        
    def __unicode__(self):
        if self:
            return ', '.join([str(self.latitude), str(self.longitude)])
        else: 
            return ''
    
    def __sub__(self,loc2):
        """ Returns a 2-tuple of distance in miles and initial bearing in
        degrees.
        """
        R = 3958.8
        dlat = radians(loc2.latitude-self.latitude)
        lat1 = radians(self.latitude)
        lat2 = radians(loc2.latitude)
        dlon = radians(loc2.longitude-self.longitude)
        a = sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2*atan2(sqrt(a),sqrt(1-a))
        d = R*c
        bearing = atan2(sin(dlon)*cos(lat2),cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(dlon))
        return d, (degrees(bearing)+360) % 360
    def __len__(self):
        if self.latitude is None or self.longitude is None:
            return 0
        else:
            return 1
class MapWidget(forms.TextInput):
    class Media:
        js = ('https://maps.googleapis.com/maps/api/js?key=AIzaSyBcW7EQwfPZa3poz2Hr3MPllP4vjpilcLc',)
    def render(self,name,value,attrs=None):
        if isinstance(value, GeoLocation):
            loc = value
        else:
            try:
                loc = GeoLocation.from_string(value)
            except ValidationError:
                value = None
                loc = GeoLocation(None,None)
        latitude = loc.latitude or 42.260
        longitude = loc.longitude or -83.7483
        input_html = super(MapWidget, self).render(name,value,attrs)

        return mark_safe(input_html+'\n'+unicode(self.media)+r'''
<div id="map-canvas" style="width:400px; height:400px;"></div>
<script>
var map;
var marker;
var infowindow;
function initialize() {
    var mapOptions = {
        center: { lat: %(lat)f, lng: %(lng)f},
        zoom: %(z)d,
        mapTypeId: google.maps.MapTypeId.HYBRID
    };
    map = new google.maps.Map(document.getElementById('map-canvas'),
        mapOptions);
    $('[name="%(name)s"]').hide()
    google.maps.event.addListener(map, 'click', function(event) {
        addMarker(event.latLng);
        var lat = Math.round(1000000*event.latLng.lat())/1000000;
        var lng = Math.round(1000000*event.latLng.lng())/1000000;
        $('[name="%(name)s"]').val(lat.toString()+', '+lng.toString());
    });
    if(%(is_existing)s){
        addMarker({ lat: %(lat)f, lng: %(lng)f});
    }
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
        title: 'My Location'
    });
    infowindow = new google.maps.InfoWindow({
        content: marker.title
    });
    infowindow.open(marker.get('map'), marker);
    google.maps.event.addListener(marker, 'click', function() {
        infowindow.open(marker.get('map'), marker);
    });
}
</script>    
'''%{   'lat': latitude,
        'lng': longitude,
        'name': name,
        'is_existing': 'true' if (loc.latitude is not None) else 'false',
        'z': 10 if loc.latitude is None else 18,
    })

class LocationFormField(forms.CharField):
    widget = MapWidget
    def clean(self,value):
        v=super(LocationFormField, self).clean(value)
        if v is None:
            return v
        ll = value.split(',')
        if len(ll) != 2:
            raise ValidationError(_('Location must be a latitude/longitude pair.'))
        try:
            latitude = Decimal(ll[0].strip())
            longitude = Decimal(ll[1].strip())
        except InvalidOperation:
            raise ValidationError(_('Could not convert entries to decimal.'))
        if latitude > 90 or latitude < -90:
            raise ValidationError(_('Latitude must be in [-90,90]'))
        if longitude > 180 or longitude < -180:
            raise ValidationError(_('Longitude must be in [-180,180]'))
        return v
class LocationField(with_metaclass(models.SubfieldBase, models.CharField)):
    """ A Location (latitude and longitude)."""
    
    description = _('A comma-separated pair of decimal values representing'
                    'latitude and longitude')
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 22
        super(LocationField, self).__init__(*args,**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(LocationField, self).deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def to_python(self, value):
        if isinstance(value, GeoLocation):
            return value
        
        if value is None or value == '':
            return GeoLocation(None, None)
        # The string case
        ll = value.split(',')
        if len(ll) != 2:
            raise ValidationError("Invalid input for GeoLocation instance %s"%unicode(ll))
        latitude = Decimal(ll[0].strip())
        longitude = Decimal(ll[1].strip())
        return GeoLocation(latitude, longitude)

    def get_prep_value(self,value):
        return unicode(value)
        
    def formfield(self, **kwargs):
        defaults = {'form_class':LocationFormField}
        defaults.update(kwargs)
        return super(LocationField, self).formfield(**defaults)