from django.conf.urls import patterns, url

from electees import views


urlpatterns = patterns('',
    url(r'^edit_electee_group_membership/$', views.edit_electee_group_membership, name='edit_electee_group_membership'),
    url(r'^electee_groups/$', views.view_electee_groups,name='view_electee_groups'),
    url(r'^edit_electee_groups/$', views.edit_electee_groups,name='edit_electee_groups'),
    url(r'^edit_electee_group_points/$', views.edit_electee_group_points,name='edit_electee_group_points'),
    url(r'^edit_electee_resources/$', views.edit_electee_resources,name='edit_electee_resources'),
    url(r'^submit_education_form/$', views.submit_background_form,name='submit_background_form'),
    url(r'^edit_electee_survey/(?P<term_id>\d+)/$', views.edit_survey_for_term,name='edit_survey_for_term'),
    url(r'^edit_electee_survey/$', views.edit_survey,name='edit_survey'),
    url(r'^manage_survey/$', views.manage_survey,name='manage_survey'),
    url(r'^edit_survey_parts/$', views.edit_survey_parts,name='edit_survey_parts'),
    url(r'^edit_survey_questions/$', views.edit_survey_questions,name='edit_survey_questions'),
    url(r'^add_survey_questions_for_term/(?P<term_id>\d+)/$', views.add_survey_questions_for_term,name='add_survey_questions_for_term'),
    url(r'^add_survey_questions/$', views.add_survey_questions,name='add_survey_questions'),
    url(r'^preview_survey_for_term/(?P<term_id>\d+)/$', views.preview_survey_for_term,name='preview_survey_for_term'),
    url(r'^preview_survey/$', views.preview_survey,name='preview_survey'),
    url(r'^complete_survey_for_term/(?P<term_id>\d+)/$', views.complete_survey_for_term,name='complete_survey_for_term'),
    url(r'^complete_survey/$', views.complete_survey,name='complete_survey'),
    url(r'^interview_followup/(?P<interview_id>\d+)/$', views.complete_interview_followup,name='complete_interview_followup'),
    url(r'^my_interview_forms/$', views.view_my_interview_forms,name='view_my_interview_forms'),
    url(r'^view_interview_followup/(?P<follow_up_id>\d+)/$', views.view_interview_follow_up,name='view_interview_follow_up'),
    
)
