"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from about.tests.factories import *
from mig_main.models import AcademicTerm,OfficerPosition,UserProfile
from migweb.test_tools import MyClient

JOINING_HTML=r'''<h1>A First Level Header</h1>
<h2>A Second Level Header</h2>
<p>Now is the time for all good men to come to<br />
the aid of their country. This is just a<br />
regular paragraph.</p>
<p>The quick brown fox jumped over the lazy<br />
dog's back.</p>
<h3>Header 3</h3>
<blockquote>
<p>This is a blockquote.</p>
<p>This is the second paragraph in the blockquote.</p>
<h2>This is an H2 in a blockquote</h2>
</blockquote>'''

class AboutViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = MyClient()
        self.user =User.objects.create_user('johndoe','johndoe@umich.edu','password')
        self.admin =User.objects.create_superuser('jimharb','jimharb@umich.edu','password')
            
        
    
        self.terms=AcademicTermFactory.create_batch(18)
        self.chapters=TBPChapterFactory.create_batch(3)
        self.standings=StandingFactory.create_batch(3)
        self.statuses=StatusFactory.create_batch(3)
        self.majors=MajorFactory.create_batch(3)
        self.shirt_sizes=ShirtSizeFactory.create_batch(3)
        self.current_term=CurrentTermFactory()
        

    def tearDown(self):
        pass

    def test_views_index(self):
        #base about
        view_url = reverse('about:index')
        client = self.client
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        
        # Test that the context is correct
        self.assertTrue('can_edit_about_photos' in context)
        self.assertFalse(context['can_edit_about_photos'])
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'],'about')
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'],'about')
        self.assertTrue('slideshow_photos' in context)
        self.assertFalse(context['slideshow_photos'].exists())
        
        # Test non-admin permissions
        login = self.client.login(username=self.user.username,password='password')

        self.assertTrue(login)
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('can_edit_about_photos' in context)
        self.assertFalse(context['can_edit_about_photos'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.user)
        client.logout()
        
        # Test admin permissions
        self.assertTrue(client.login(username=self.admin.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('can_edit_about_photos' in context)
        self.assertTrue(context['can_edit_about_photos'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.admin)
        client.logout()
        
        # Test photos
        photo1=AboutPhotoFactory()
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('slideshow_photos' in context)
        self.assertTrue(context['slideshow_photos'].exists())
        self.assertEqual(context['slideshow_photos'][0],photo1)
        photo1.active=False
        photo1.save()
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('slideshow_photos' in context)
        self.assertFalse(context['slideshow_photos'].exists())
        
        photo2=AboutPhotoFactory()
        
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('slideshow_photos' in context)
        self.assertFalse(context['slideshow_photos'].exists())
        
        photo1.active=True
        photo1.save()
        photo2.active=True
        photo2.save()
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('slideshow_photos' in context)
        self.assertTrue(context['slideshow_photos'].exists())
        self.assertEqual(context['slideshow_photos'].count(),2)
    def test_views_joining(self):  
        client = self.client  
        #joining
        view_url = reverse('about:eligibility')
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('eligibility_text' in resp.context)
        self.assertEqual(resp.context['eligibility_text'].count(),0)
        self.assertTrue('ugrad_text' in resp.context)
        self.assertEqual(resp.context['ugrad_text'].count(),0)
        self.assertTrue('grad_text' in resp.context)
        self.assertEqual(resp.context['grad_text'].count(),0)
        self.assertTrue('why_join_text' in resp.context)
        self.assertEqual(resp.context['why_join_text'].count(),0)
        self.assertTrue('can_edit_page' in resp.context)
        self.assertFalse(resp.context['can_edit_page'])
        self.assertTrue('subnav' in resp.context)
        self.assertEqual(resp.context['subnav'],'joining')
        self.assertTrue('main_nav' in resp.context)
        self.assertEqual(resp.context['main_nav'],'about')

        # Test non-admin permissions
        login = self.client.login(username=self.user.username,password='password')

        self.assertTrue(login)
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('can_edit_page' in context)
        self.assertFalse(context['can_edit_page'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.user)
        client.logout()
        
        # Test admin permissions
        self.assertTrue(client.login(username=self.admin.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('can_edit_page' in context)
        self.assertTrue(context['can_edit_page'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.admin)
        client.logout()
        
        # Test Officer Permissions
        officers = OfficerFactory.create_batch(NUM_OFFICERS)
        for officer in officers:
            self.assertTrue(client.login(username=officer.user.user.username,password='password'))
            resp = client.get(view_url)
            self.assertEqual(resp.status_code,200)
            context = resp.context
            self.assertTrue('user' in context)
            self.assertEqual(context['user'],officer.user.user)
            self.assertTrue('can_edit_page' in context)
            if officer.position.name in ['President','Vice President','Graduate Student Vice President']:
                self.assertTrue(context['can_edit_page'],msg='%s unable to edit'%unicode(officer.position))
            else:
                self.assertFalse(context['can_edit_page'],msg='%s able to edit'%unicode(officer.position))
            client.logout()
        # Test Joining Content
        joining_sections = JoiningTextFactory.create_batch(4)
        resp = client.get(view_url)
        self.assertTrue('eligibility_text' in resp.context)
        self.assertEqual(resp.context['eligibility_text'].count(),1)
        self.assertEqual(resp.context['eligibility_text'][0].text,JOINING_TEXT)
        self.assertEqual(resp.context['eligibility_text'][0].section,'EL')
        self.assertTrue('ugrad_text' in resp.context)
        self.assertEqual(resp.context['ugrad_text'].count(),1)
        self.assertEqual(resp.context['ugrad_text'][0].text,JOINING_TEXT)
        self.assertEqual(resp.context['ugrad_text'][0].section,'UG')
        self.assertTrue('grad_text' in resp.context)
        self.assertEqual(resp.context['grad_text'].count(),1)
        self.assertEqual(resp.context['grad_text'][0].text,JOINING_TEXT)
        self.assertEqual(resp.context['grad_text'][0].section,'GR')
        self.assertTrue('why_join_text' in resp.context)
        self.assertEqual(resp.context['why_join_text'].count(),1)
        self.assertEqual(resp.context['why_join_text'][0].text,JOINING_TEXT)
        self.assertEqual(resp.context['why_join_text'][0].section,'Y')
        self.assertTrue(JOINING_HTML in resp.content,msg='Markdown not working correctly')
    def test_views_bylaws(self):  
        #bylaws
        view_url = reverse('about:bylaws')
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('documents' in resp.context)
        self.assertEqual(resp.context['documents'].count(),0)
        self.assertTrue('main_nav' in resp.context)
        self.assertEqual(resp.context['main_nav'],'about')
        self.assertTrue('subnav' in resp.context)
        self.assertEqual(resp.context['subnav'],'bylaws')
        doc_types =DocumentTypeFactory.create_batch(2)
        inactive_docs = OldDocumentFactory.create_batch(5)
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('documents' in resp.context)
        self.assertEqual(resp.context['documents'].count(),0)
        
        inactive_docs = CurrentDocumentFactory.create_batch(2)
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('documents' in resp.context)
        self.assertEqual(resp.context['documents'].count(),2)
        
        
    def test_views_leadership(self):    
        #leadership
        
        view_url = reverse('about:leadership')
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('officers' in resp.context)
        self.assertTrue('officers' in resp.context['officers'])
        self.assertEqual(len(resp.context['officers']['officers']),0)
        self.assertTrue('advisors' in resp.context['officers'])
        self.assertFalse(resp.context['officers']['advisors'].exists())
        self.assertTrue('committee_members' in resp.context)
        self.assertFalse(resp.context['committee_members'].exists())
        self.assertTrue('officer_ids' in resp.context)
        self.assertFalse(resp.context['officer_ids'].exists())
        self.assertTrue('terms' in resp.context)
        self.assertTrue(resp.context['terms'].exists())
        self.assertEqual(resp.context['terms'].count(),5)
        self.assertTrue('requested_term' in resp.context)
        self.assertEqual(resp.context['requested_term'],AcademicTerm.get_current_term())
        self.assertTrue('is_current' in resp.context)
        self.assertTrue(resp.context['is_current'])
        self.assertTrue('subnav' in resp.context)
        self.assertEqual(resp.context['subnav'],'leadership')
        self.assertTrue('main_nav' in resp.context)
        self.assertEqual(resp.context['main_nav'],'about')
        
        
        officers = OfficerFactory.create_batch(NUM_OFFICERS)
        teams = OfficerTeamFactory.create_batch(4)
        resp = self.client.get(view_url)
        self.assertEqual(resp.status_code,200)
        self.assertTrue('officers' in resp.context)
        self.assertTrue('officers' in resp.context['officers'])
        self.assertEqual(len(resp.context['officers']['officers']),4)
        #test individual teams--further testing should be done in pack_officers method
        for team in resp.context['officers']['officers']:
            if team['name'] =='Executive Committee':
                self.assertEqual(team['order'],0)
            else:
                self.assertNotEqual(team['order'],0)
        self.assertTrue('advisors' in resp.context['officers'])
        self.assertEqual(resp.context['officers']['advisors'].count(),1)
        self.assertTrue('committee_members' in resp.context)
        self.assertFalse(resp.context['committee_members'].exists())
        self.assertTrue('officer_ids' in resp.context)
        self.assertEqual(resp.context['officer_ids'].count(),NUM_OFFICERS)
        # Test committees -- TODO
        
    def test_update_photos(self):
        view_url = reverse('about:update_about_photos')
        client = self.client
        resp = self.client.get(view_url,follow=True)
        self.assertEqual(len(resp.redirect_chain),1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1],302)
        self.assertTrue(reverse('about:index') in med[0])
        self.assertTrue('error_message' in resp.context)
        #no one without a profile should have access
        self.assertTrue(client.login(username=self.user.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,302)
        client.logout()
        #no non-member should be able to access
        generic_user = UserProfileFactory()
        self.assertTrue(client.login(username=generic_user.user.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,302)
        client.logout()
        #no general member should be able to access
        generic_member = MemberProfileFactory()
        self.assertTrue(client.login(username=generic_member.user.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,302)
        client.logout()
        #no officer should be able to access unless they are an admin
        officers = OfficerFactory.create_batch(NUM_OFFICERS)
        for officer in officers:
            self.assertTrue(client.login(username=officer.user.user.username,password='password'))
            resp = client.get(view_url)
            self.assertEqual(resp.status_code,302)
            client.logout()
        #admin should be able to access
        self.assertTrue(client.login(username=self.admin.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('formset' in context)
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'],'about')
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'],'about')
        self.assertTrue('prefix' in context)
        self.assertEqual(context['prefix'],'about_photo')
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.admin)
        marble = open('about/tests/test_photos/about_marbles.jpg')
        post_data = {
          'about_photo-TOTAL_FORMS':u'1',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'0',
          'about_photo-0-id':u'',
          'about_photo-0-active':u'1',
          'about_photo-0-title':u'Title',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':marble,
          'about_photo-0-DELETE':u'0',
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(resp.status_code,200)
        self.assertFalse(resp.context['error_message'])
        client.logout()
    def test_update_joining(self):
        pass
    def test_leadership_other_term(self):
        pass
    def test_officer_ajax(self):
        pass