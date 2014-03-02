from django.conf.urls import patterns, url

from fora import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
)
