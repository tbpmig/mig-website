from django.conf.urls import patterns, url

from member_resources import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^profiles/$',views.member_profiles, name='member_profiles'),
	url(r'^profiles/(?P<uniqname>[a-z]{3,8})/$',views.profile, name='profile'),
	url(r'^profiles/(?P<uniqname>[a-z]{3,8})/edit/$',views.profile_edit, name='profile_edit'),
    url(r'^profiles/create$',views.profile_create, name='profile_create'),
    url(r'^progress/(?P<uniqname>[a-z]{3,8})/$',views.view_progress,name='view_progress'),
    url(r'^track_my_progress/$',views.track_my_progress,name='track_my_progress'),
    url(r'^edit_progress/(?P<uniqname>[a-z]{3,8})/$',views.edit_progress,name='edit_progress'),
    url(r'^progress_list/$',views.view_progress_list,name='view_progress_list'),
    url(r'^progress_table/$',views.view_progress_table,name='view_progress_table'),
    url(r'^manage_misc_reqs/$',views.view_misc_reqs,name='view_misc_reqs'),
    url(r'^history_reports/$',views.access_history,name='access_history'),
    url(r'^approve_tutoring/$',views.approve_tutoring_forms,name='approve_tutoring_forms'),
    url(r'^electees_stopping_electing/$', views.handle_electees_stopping_electing,name='handle_electees_stopping_electing'),
    url(r'^manage_active_group_meetings/$',views.manage_active_group_meetings,name='manage_active_group_meetings'),
    url(r'^manage_project_leaders/$',views.manage_project_leaders,name='manage_project_leaders'),
    url(r'^add_active_statuses/$',views.add_active_statuses,name='add_active_statuses'),
    url(r'^add_active_statuses_for_term/(?P<term_id>\d+)/$',views.add_active_statuses_for_term,name='add_active_statuses_for_term'),
    url(r'^edit_active_statuses/$',views.manage_active_statuses,name='manage_active_statuses'),
    url(r'^move_electees_to_active/$',views.move_electees_to_active,name='move_electees_to_active'),
    url(r'^add_electee_DAPA/$',views.add_electee_DA_PA_status,name='add_electee_DA_PA_status'),
    url(r'^add_leadership_credit/$',views.add_leadership_credit,name='add_leadership_credit'),
    url(r'^change_requirements/(?P<distinction_id>\d+)/$',views.change_requirements,name='change_requirements'),
    url(r'^change_event_categories/$',views.change_event_categories,name='change_event_categories'),
    url(r'^manage_officers/(?P<term_id>\d+)/$',views.manage_officers,name='manage_officers'),
    url(r'^meeting_feedback/(?P<term_id>\d+)/$',views.view_meeting_feedback_for_term,name='view_meeting_feedback_for_term'),
    url(r'^meeting_feedback/$',views.view_meeting_feedback,name='view_meeting_feedback'),
    url(r'^manage_dues/$',views.manage_dues,name='manage_dues'),
    url(r'^add_actives/$',views.add_to_active_list,name='add_to_active_list'),
    url(r'^edit_member_lists/$',views.edit_list,name='edit_list'),
    url(r'^clear_electee_lists/$',views.clear_electee_lists,name='clear_electee_lists'),
    url(r'^add_ugrad_electees/$',views.add_to_ugrad_electee_list,name='add_to_ugrad_electee_list'),
    url(r'^add_grad_electees/$',views.add_to_grad_electee_list,name='add_to_grad_electee_list'),
    url(r'^manage_website/$',views.manage_website,name='manage_website'),
    url(r'^advance_term/$',views.advance_term,name='advance_term'),
    url(r'^manage_electee_paperwork/$',views.manage_electee_paperwork,name='manage_electee_paperwork'),
    url(r'^download_active_progress/$',views.download_active_progress,name='download_active_progress'),
    url(r'^download_grad_el_progress/$',views.download_grad_el_progress,name='download_grad_el_progress'),
    url(r'^download_ugrad_el_progress/$',views.download_ugrad_el_progress,name='download_ugrad_el_progress'),
    url(r'^officer_minutes/$',views.officer_meeting_minutes,name='officer_meeting_minutes'),
    url(r'^advisory_board_minutes/$',views.advisory_board_meeting_minutes,name='advisory_board_meeting_minutes'),
    url(r'^meeting_minutes/$',views.main_meeting_minutes,name='main_meeting_minutes'),
    url(r'^NI_minutes/$',views.new_initiatives_meeting_minutes,name='new_initiatives_meeting_minutes'),
    url(r'^committee_minutes/$',views.committee_meeting_minutes,name='committee_meeting_minutes'),
    url(r'^upload_minutes/$',views.upload_minutes,name='upload_minutes'),
    url(r'^update_preferences/$',views.update_preferences,name='update_preferences'),
    url(r'^list_project_reports/$',views.project_reports_list,name='project_reports_list'),
    url(r'^add_external_service/$',views.add_external_service,name='add_external_service'),
    url(r'^grad_background_forms/$',views.view_background_forms,name='view_background_forms'),
    url(r'^give_tbpraise/$',views.submit_praise,name='submit_praise'),
    url(r'^approve_tbpraise/(?P<praise_id>\d+)/$',views.approve_praise,name='approve_praise'),
    url(r'^new_non_event_project/$',views.new_non_event_project,name='new_non_event_project'),
    url(r'^non_event_project/(?P<ne_id>\d+)/$',views.non_event_project,name='non_event_project'),
    url(r'^non_event_project_participants/(?P<ne_id>\d+)/$',views.non_event_project_participants,name='non_event_project_participants'),
    url(r'^manage_awards/(?P<term_id>\d+)/$',views.manage_awards_for_term,name='manage_awards_for_term'),
    url(r'^manage_awards/$',views.manage_awards,name='manage_awards'),
    url(r'^view_electee_surveys/(?P<term_id>\d+)/$',views.view_electee_surveys_for_term,name='view_electee_surveys_for_term'),
    url(r'^view_electee_surveys/$',views.view_electee_surveys,name='view_electee_surveys'),
    url(r'^manage_background_checks/$',views.add_background_checks,name='add_background_checks'),
    url(r'^manage_many_background_checks/$',views.mass_add_background_checks,name='mass_add_background_checks'),
    url(r'^download_member_data/$',views.download_member_data,name='download_member_data'),
    url(r'^download_member_data_email/$',views.download_member_data_email,name='download_member_data_email'),
    url(r'^download_active_status/$',views.download_active_status,name='download_active_status'),
    url(r'^download_elections_voters/$',views.download_elections_voters,name='download_elections_voters'),
    url(r'^view_electee_survey/(?P<uniqname>[a-z]{3,8})/$',views.view_electee_survey,name='view_electee_survey'),
    url(r'^manage_committee_members/(?P<term_id>\d+)/$',views.manage_committee_members,name='manage_committee_members'),
    url(r'^manage_committees/$',views.manage_committees,name='manage_committees'),
    url(r'^view_photos/$',views.view_photos,name='view_photos'),
    
)
