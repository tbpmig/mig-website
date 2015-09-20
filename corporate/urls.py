from django.conf.urls import patterns, url

from corporate import views

urlpatterns = patterns('',
	url(r'^$',views.index, name='index'),
	url(r'^resumes/$',views.resumes, name='resumes'),
	url(r'^edit/$',views.update_corporate_page, name='update_corporate_page'),
	url(r'^update_resource_guide/$',views.update_resource_guide, name='update_resource_guide'),
	url(r'^add_contact/$',views.add_company_contact, name='add_company_contact'),
	url(r'^add_company/$',views.add_company, name='add_company'),
	url(r'^add_industry/$',views.add_jobfield, name='add_jobfield'),
	url(r'^edit_contacts/$',views.edit_company_contacts, name='edit_company_contacts'),
	url(r'^update_corporate_email/$',views.update_corporate_email, name='update_corporate_email'),
	url(r'^view_contacts/$',views.view_company_contacts, name='view_company_contacts'),
	url(r'^view_and_send_email/$',views.view_and_send_email, name='view_and_send_email'),
	url(r'^send_email_to_companies/$',views.send_corporate_email, name='send_corporate_email'),
)
