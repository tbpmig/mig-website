from django.conf.urls import patterns, url

from fora import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
    url(r'^add_comment/(?P<forum_id>\d+)-(?P<reply_to_id>\d+)/$',views.add_comment,name='add_comment'),
    url(r'^add_thread/(?P<forum_id>\d+)/$',views.create_thread,name='create_thread'),
    url(r'^view_thread/(?P<thread_id>\d+)/$',views.view_thread,name='view_thread'),
    url(r'^new_forum/$',views.create_forum,name='create_forum'),
)
