from django.conf.urls import patterns, url

from history import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^article/(?P<article_id>\d+)/$',views.article_view,name='article_view'),
	url(r'^cornerstone/$',views.cornerstone_view,name='cornerstone_view'),
	url(r'^alumninews/$',views.alumninews_view,name='alumninews_view'),
    url(r'^upload_article/$',views.upload_article,name='upload_article'),
	url(r'^start_project_reports/(?P<term_id>\d+)/$',views.start_project_report_compilation,name='start_project_report_compilation'),
	url(r'^process_reports/(?P<prh_id>\d+)-(?P<pr_id>\d+)/$',views.process_project_reports,name='process_project_reports'),
	url(r'^process_report_photos/(?P<prh_id>\d+)-(?P<pr_id>\d+)/$',views.process_project_report_photos,name='process_project_report_photos'),
)
