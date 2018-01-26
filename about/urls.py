from django.conf.urls import  url

from about import views

urlpatterns = [
    url(r'^$',
        views.index,
        name='index'),
    url(r'^eligibility/$',
        views.eligibility,
        name='eligibility'),
    url(r'^joining_edit/$',
        views.update_joining_page,
        name='update_joining_page'),
    url(r'^update_about_photos/$',
        views.update_about_photos,
        name='update_about_photos'),
    url(r'^update_bylaws/$',
        views.update_bylaws,
        name='update_bylaws'),
    url(r'^bylaws/$',
        views.bylaws,
        name='bylaws'),
    url(r'^leadership/(?P<term_id>\d+)/$',
        views.leadership_for_term,
        name='leadership_for_term'),
    url(r'^officer_ajax/(?P<officer_id>\d+)/$',
        views.officer,
        name='officer'),
    url(r'^leadership/$',
        views.leadership,
        name='leadership'),
]
