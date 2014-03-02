from django.conf.urls import patterns, url

from event_cal import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^event_list/$',views.list, name='list'),
	url(r'^generate_announcements/$',views.generate_announcements, name='generate_announcements'),
	url(r'^add_announcement/$',views.add_announcement, name='add_announcement'),
	url(r'^tutoring_form/$',views.submit_tutoring_form, name='submit_tutoring_form'),
	url(r'^my_events/$',views.my_events, name='my_events'),
    url(r'^create_event/$',views.create_event, name='create_event'),
    url(r'^add_event_photo/$',views.add_event_photo, name='add_event_photo'),
    url(r'^create_meeting_signin/(?P<event_id>\d+)/$',views.create_meeting_signin, name='create_meeting_signin'),
    url(r'^delete_event/(?P<event_id>\d+)/$',views.delete_event, name='delete_event'),
    url(r'^event_project_report/(?P<event_id>\d+)/$',views.event_project_report, name='event_project_report'),
    url(r'^project_report_by_id/(?P<report_id>\d+)/$',views.project_report_by_id, name='project_report_by_id'),
    url(r'^edit_event/(?P<event_id>\d+)/$',views.edit_event, name='edit_event'),
    url(r'^carpool_sign_up/(?P<event_id>\d+)/$',views.carpool_sign_up, name='carpool_sign_up'),
    url(r'^complete_event/(?P<event_id>\d+)/$',views.complete_event, name='complete_event'),
    #url(r'^complete_signin_event/(?P<event_id>\d+)/$',views.complete_event2, name='complete_event2'),
    url(r'^update_event/(?P<event_id>\d+)/$',views.update_completed_event, name='update_completed_event'),
    url(r'^delete_shift/(?P<event_id>\d+)-(?P<shift_id>\d+)/$',views.delete_shift, name='delete_shift'),
    url(r'event/(?P<event_id>\d+)/$',views.event_detail, name='event_detail'),
    # don't change this order-- YAY regex!
    url(r'unsign_up/(?P<event_id>\d+)-(?P<shift_id>\d+)/$',views.unsign_up, name='unsign_up'),
    url(r'sign_up/(?P<event_id>\d+)-(?P<shift_id>\d+)/$',views.sign_up, name='sign_up'),
    url(r'meeting_sign_in/(?P<event_id>\d+)-(?P<shift_id>\d+)/$',views.meeting_sign_in, name='meeting_sign_in'),
    url(r'authorize_google_cal/',views.gcal_test,name='gcal_test'),
	url(r'^add_project_report/$',views.project_report, name='project_report'),
    url(r'^event_attach_report/(?P<event_id>\d+)/$',views.add_project_report_to_event, name='add_project_report_to_event'),
	#url(r'^leadership/$',views.leadership, name='leadership'),
	#url(r'^bylaws/$',views.bylaws, name='bylaws'),
)
