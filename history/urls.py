from django.conf.urls import patterns, url

from history import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^article/(?P<article_id>\d+)/$',views.article_view,name='article_view'),
	url(r'^cornerstone/$',views.cornerstone_view,name='cornerstone_view'),
	url(r'^alumninews/$',views.alumninews_view,name='alumninews_view'),
    url(r'^upload_article/$',views.upload_article,name='upload_article'),
)
