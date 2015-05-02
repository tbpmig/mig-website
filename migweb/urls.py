from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^$', 'migweb.views.home', name='home'),
	url(r'^career_fair/companies/$', 'migweb.views.cf_companies', name='cf_companies'),
	url(r'^about/',include('about.urls', namespace='about')),
	url(r'^outreach/',include('outreach.urls', namespace='outreach')),
	url(r'^publications/',include('history.urls', namespace='history')),
	url(r'^corporate/',include('corporate.urls', namespace='corporate')),
	url(r'^calendar/',include('event_cal.urls', namespace='event_cal')),
	url(r'^members/elections/',include('elections.urls', namespace='elections')),
    url(r'^members/electees/',include('electees.urls',namespace='electees')),
	url(r'^members/playground/',include('fora.urls', namespace='fora')),
	url(r'^members/',include('member_resources.urls', namespace='member_resources')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', 'migweb.views.login_view', name='login_view'),
	url(r'^accounts/login/$', 'django.contrib.auth.views.login',{'template_name': 'mig_main/login.html'}),
	url(r'^accounts/logout/$', 'migweb.views.logout_view', name='logout'),
    url(r'^oauth2callback/$','event_cal.views.oauth',name='oauth'),
    url(r'^townhalls/$',RedirectView.as_view(url='/outreach/townhalls/')),
    url(r'^pi_day/$',RedirectView.as_view(url='/outreach/pi_day/')),
    url(r'^pi-day/$',RedirectView.as_view(url='/outreach/pi_day/')),
    url(r'^piday/$',RedirectView.as_view(url='/outreach/pi_day/')),
    url(r'^twitter_oauth/$','migweb.views.twitter_oauth',name='twitter_oauth'),
    url(r'^init_twitter/$','migweb.views.initialize_twitter',name='initialize_twitter'),
    url(r'^slide_ajax/(?P<slide_id>\d+)/$','migweb.views.get_slide_ajax',name='get_slide_ajax'),
    url(r'^photo_ajax/(?P<photo_id>\d+)/$','migweb.views.get_eventphoto_ajax',name='get_eventphoto_ajax'),
    url(r'^article_photo_ajax/(?P<photo_id>\d+)/$','migweb.views.get_article_photo_ajax',name='get_article_photo_ajax'),
    #url(r'^settings/',include('dbsettings.urls')),
)+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
