from django.conf.urls import patterns, url

from elections import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
    url(r'^(?P<election_id>\d+)/officer_positions/$',views.positions,name='positions'),
	url(r'^(?P<election_id>\d+)/$',views.list, name='list'),
	url(r'^(?P<election_id>\d+)/nominate/$',views.nominate, name='nominate'),
	#url(r'^(?P<term_name>\d+)/nominate_candidate/$',views.temp_nominate, name='temp_nominate'),
	url(r'^(?P<nomination_id>\d+)/acceptdecline/$',views.accept_or_decline_nomination, name='accept_or_decline_nomination'),
	url(r'^(?P<election_id>\d+)/my_nominations/$',views.my_nominations, name='my_nominations'),
    #url(r'^my_nominations/$',views.my_nominations,name='my_nominations'),
	#url(r'^(?P<term_name>[W,F]\d+)/submitnominate/$',views.submit_nomination, name='submit_nomination')
)
