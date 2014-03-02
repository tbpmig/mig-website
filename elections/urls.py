from django.conf.urls import patterns, url

from elections import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^(?P<term_name>\d+)/$',views.list, name='list'),
	url(r'^(?P<term_name>\d+)/nominate/$',views.nominate, name='nominate'),
	url(r'^(?P<term_name>\d+)/nominate_candidate/$',views.temp_nominate, name='temp_nominate'),
	url(r'^(?P<term_name>\d+)/acceptdecline/$',views.accept_or_decline_nomination, name='accept_or_decline_nomination'),
	#url(r'^(?P<term_name>[W,F]\d+)/submitnominate/$',views.submit_nomination, name='submit_nomination')
)
