from django.conf.urls import patterns, url

from corporate import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^resumes/$',views.resumes, name='resumes'),
	url(r'^edit/$',views.update_corporate_page, name='update_corporate_page'),
	url(r'^update_resource_guide/$',views.update_resource_guide, name='update_resource_guide'),
)
