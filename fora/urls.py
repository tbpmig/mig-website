from django.conf.urls import patterns, url

from fora import views

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='index'),
    url(r'^add_comment/(?P<forum_id>\d+)-(?P<reply_to_id>\d+)/$',
        views.add_comment, name='add_comment'),
    url(r'^add_thread/(?P<forum_id>\d+)/$',
        views.create_thread, name='create_thread'),
    url(r'^view_thread/(?P<thread_id>\d+)/$',
        views.view_thread, name='view_thread'),
    url(r'^hide_comment/(?P<comment_id>\d+)/$',
        views.hide_comment, name='hide_comment'),
    url(r'^upvote_comment/(?P<comment_id>\d+)/$',
        views.upvote_comment, name='upvote_comment'),
    url(r'^downvote_comment/(?P<comment_id>\d+)/$',
        views.downvote_comment, name='downvote_comment'),
    url(r'^withdraw_upvote/(?P<comment_id>\d+)/$',
        views.withdraw_upvote, name='withdraw_upvote'),
    url(r'^withdraw_downvote/(?P<comment_id>\d+)/$',
        views.withdraw_downvote, name='withdraw_downvote'),
    url(r'^new_forum/$', views.create_forum, name='create_forum'),
    url(r'^delete_forum/(?P<forum_id>\d+)/$',
        views.delete_forum, name='delete_forum'),
    url(r'^get_thread_page/(?P<forum_id>\d+)-(?P<page_num>\d+)/$',
        views.get_thread_page, name='get_thread_page'),
    url(r'^map/$', views.view_map, name='view_map'),
)
