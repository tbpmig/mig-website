from django.conf.urls import patterns, url

from django.views.generic import RedirectView
from outreach import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^mindset/$',views.mindset, name='mindset'),
	url(r'^edit_mindset_modules/$',views.update_mindset_modules, name='update_mindset_modules'),
	url(r'^edit_mindset_photos/$',views.update_mindset_photos, name='update_mindset_photos'),
	url(r'^update_mindset_profile_additions/$',views.update_mindset_profile_additions, name='update_mindset_profile_additions'),
	url(r'^tutoring/$',views.tutoring, name='tutoring'),
	url(r'^hide_event/(?P<url_stem>[a-z,_]+)/$',views.hide_outreach_event, name='hide_outreach_event'),
	url(r'^(?P<url_stem>[a-z,_]+)/$',views.outreach_event, name='outreach_event'),
)
