from django.conf.urls import patterns, url

from outreach import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^mindset/$',views.mindset, name='mindset'),
	url(r'^edit_mindset_modules/$',views.update_mindset_modules, name='update_mindset_modules'),
	url(r'^edit_mindset_photos/$',views.update_mindset_photos, name='update_mindset_photos'),
	url(r'^tutoring/$',views.tutoring, name='tutoring'),
	url(r'^townhalls/$',views.townhalls, name='townhalls'),
	url(r'^breakfast/$',views.puesdays, name='puesdays'),
)
