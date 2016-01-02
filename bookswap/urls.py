from django.conf.urls import patterns, url

from bookswap import views

urlpatterns = patterns(
    '',
    #url(r'^$', views.index, name='index'),
    url(r'^admin/start_transaction/$',
        views.start_transaction, name='start_transaction'),
	url(r'^admin/update_person/$',
        views.update_person, name='update_person'),
	url(r'^admin/create_book_type/$',
        views.create_book_type, name='create_book_type'),
	url(r'^admin/receive_book_start/(?P<uniqname>[a-z]{3,8})/$',
        views.receive_book_start, name='receive_book_start'),
	url(r'^admin/receive_book/(?P<uniqname>[a-z]{3,8})-(?P<book_type_id>\d+)/$',
        views.receive_book, name='receive_book'),
    url(r'^admin/$',
        views.admin_index, name='admin_index'),
)
