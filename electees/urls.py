from django.conf.urls import patterns, url

from electees import views


urlpatterns = patterns('',
    url(r'^edit_electee_group_membership/$', views.edit_electee_group_membership, name='edit_electee_group_membership'),
    url(r'^electee_groups/$', views.view_electee_groups,name='view_electee_groups'),
    url(r'^edit_electee_groups/$', views.edit_electee_groups,name='edit_electee_groups'),
    url(r'^edit_electee_group_points/$', views.edit_electee_group_points,name='edit_electee_group_points'),
    url(r'^edit_electee_resources/$', views.edit_electee_resources,name='edit_electee_resources'),
    url(r'^submit_education_form/$', views.submit_background_form,name='submit_background_form'),
)
