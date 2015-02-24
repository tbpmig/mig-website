"""
This contains the tests (unit and integration) for the about module.

It currently contains:
-views (complete)
"""
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from about.models import AboutSlideShowPhoto,JoiningTextField
from about.tests.factories import *
from mig_main.models import AcademicTerm,OfficerPosition,UserProfile,Major,ShirtSize,TBPChapter,Standing,Status,Major,ShirtSize
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

def setUpModule():
    print 'setting up about test data...'
    terms=AcademicTermFactory.create_batch(18)
    chapters=TBPChapterFactory.create_batch(3)
    standings=StandingFactory.create_batch(3)
    statuses=StatusFactory.create_batch(3)
    majors=MajorFactory.create_batch(3)
    shirt_sizes=ShirtSizeFactory.create_batch(3)
    current_term=CurrentTermFactory()
    OfficerFactory.create_batch(NUM_OFFICERS)
    JoiningTextFactory.create_batch(4)
    OfficerTeamFactory.create_batch(4)
    User.objects.create_user('johndoe','johndoe@umich.edu','password')
    User.objects.create_superuser('jimharb','jimharb@umich.edu','password')
   
def tearDownModule():
    """This should clear the database back to empty, 
    only those objects created in the setup method need to be deleted. I think"""
    print 'tearing down about module...'
    OfficerTeam.objects.all().delete()
    JoiningTextField.objects.all().delete()
    Officer.objects.all().delete()
    OfficerPosition.objects.all().delete()
    MemberProfile.objects.all().delete()
    AcademicTerm.objects.all().delete()
    ShirtSize.objects.all().delete()
    Major.objects.all().delete()
    Status.objects.all().delete()
    Standing.objects.all().delete()
    TBPChapter.objects.all().delete()
    User.objects.all().delete()
    print 'teardown complete.'
class AboutViewsTestCase(TestCase):

    def setUp(self):
        self.client = MyClient()
        self.user =User.objects.get(username='johndoe')
        self.admin =User.objects.get(username='jimharb')

    def tearDown(self):
        del(self.client)
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
        self.assertEqual(resp.context['eligibility_text'].count(),1)
        self.assertTrue('ugrad_text' in resp.context)
        self.assertEqual(resp.context['ugrad_text'].count(),1)
        self.assertTrue('grad_text' in resp.context)
        self.assertEqual(resp.context['grad_text'].count(),1)
        self.assertTrue('why_join_text' in resp.context)
        self.assertEqual(resp.context['why_join_text'].count(),1)
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
        officers = officers = Officer.objects.all()
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
        self.assertEqual(len(resp.context['officers']['officers']),4)
        self.assertTrue('advisors' in resp.context['officers'])
        self.assertTrue(resp.context['officers']['advisors'].exists())
        self.assertTrue('committee_members' in resp.context)
        self.assertFalse(resp.context['committee_members'].exists())
        self.assertTrue('officer_ids' in resp.context)
        self.assertTrue(resp.context['officer_ids'].exists())
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

        # test other term--should be empty
        resp = self.client.get(reverse('about:leadership_for_term',args=[AcademicTerm.objects.get(year=2011,semester_type__name='Fall').id]))
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
        self.assertEqual(resp.context['requested_term'],AcademicTerm.objects.get(year=2011,semester_type__name='Fall'))
        self.assertTrue('is_current' in resp.context)
        self.assertFalse(resp.context['is_current'])
        self.assertTrue('subnav' in resp.context)
        self.assertEqual(resp.context['subnav'],'leadership')
        self.assertTrue('main_nav' in resp.context)
        self.assertEqual(resp.context['main_nav'],'about')
        
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
        self.assertTrue(resp.context['error_message'])
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
        officers = Officer.objects.all()
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
        self.assertTrue(context['can_add_row'])
        self.assertTrue(context['has_files'])
        self.assertTrue('base' in context)
        
        #test submissions, first one that succeeds
        marble = open('about/tests/test_photos/about_marbles.jpg','rb')
        pdf_file = open('about/tests/test_docs/test.pdf','rb')
        post_data = {
          'about_photo-TOTAL_FORMS':u'1',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'0',
          'about_photo-0-id':u'',
          'about_photo-0-active':u'on',
          'about_photo-0-title':u'Title',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':marble,
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(len(resp.redirect_chain),1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1],302)
        self.assertTrue(reverse('about:index') in med[0])
        self.assertEqual(resp.status_code,200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(AboutSlideShowPhoto.objects.count(),1)
        #test submissions, missing the required fields
        post_data = {
          'about_photo-TOTAL_FORMS':u'2',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'1',
          'about_photo-0-id':u'1',
          'about_photo-0-active':u'on',
          'about_photo-0-title':u'Title',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':u'',
          'about_photo-1-id':u'',
          'about_photo-1-active':u'on',
          'about_photo-1-title':u'',
          'about_photo-1-text':u'',
          'about_photo-1-link':u'',
          'about_photo-1-photo':u'',
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertEqual(AboutSlideShowPhoto.objects.count(),1)
        self.assertFormsetError(resp,'formset',1,'title','This field is required.')
        self.assertFormsetError(resp,'formset',1,'text','This field is required.')
        self.assertFormsetError(resp,'formset',1,'photo','This field is required.')
        # test errors in an existing form
        post_data = {
          'about_photo-TOTAL_FORMS':u'2',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'1',
          'about_photo-0-id':u'1',
          'about_photo-0-title':u'',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':u'',
          'about_photo-1-id':u'',
          'about_photo-1-title':u'',
          'about_photo-1-text':u'',
          'about_photo-1-link':u'',
          'about_photo-1-photo':u'',
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertEqual(AboutSlideShowPhoto.objects.count(),1)
        self.assertFormsetError(resp,'formset',0,'title','This field is required.')
        # test that blank forms are fine
        post_data = {
          'about_photo-TOTAL_FORMS':u'2',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'1',
          'about_photo-0-id':u'1',
          'about_photo-0-title':u'New title',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':u'',
          'about_photo-1-id':u'',
          'about_photo-1-title':u'',
          'about_photo-1-text':u'',
          'about_photo-1-link':u'',
          'about_photo-1-photo':u'',
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(len(resp.redirect_chain),1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1],302)
        self.assertTrue(reverse('about:index') in med[0])
        self.assertEqual(resp.status_code,200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(AboutSlideShowPhoto.objects.count(),1)
        #test submissions, wrong file type
        post_data = {
          'about_photo-TOTAL_FORMS':u'2',
          'about_photo-MAX_NUM_FORMS':u'',
          'about_photo-INITIAL_FORMS':u'1',
          'about_photo-0-id':u'1',
          'about_photo-0-active':u'on',
          'about_photo-0-title':u'New title',
          'about_photo-0-text':u'Test text',
          'about_photo-0-link':u'',
          'about_photo-0-photo':u'',
          'about_photo-1-id':u'',
          'about_photo-1-title':u'Title thing',
          'about_photo-1-text':u'blah',
          'about_photo-1-link':u'',
          'about_photo-1-photo':pdf_file,
        }
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertEqual(AboutSlideShowPhoto.objects.count(),1)
        self.assertFormsetError(resp,'formset',1,'photo','Upload a valid image. The file you uploaded was either not an image or a corrupted image.')
        client.logout()
    def test_update_joining(self):
        view_url = reverse('about:update_joining_page')
        client = self.client
        resp = self.client.get(view_url,follow=True)
        self.assertEqual(len(resp.redirect_chain),1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1],302)
        self.assertTrue(reverse('about:eligibility') in med[0])
        self.assertTrue(resp.context['error_message'])
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
        #only a few officers can access it
        officers = Officer.objects.all()
        for officer in officers:
            self.assertTrue(client.login(username=officer.user.user.username,password='password'))
            resp = client.get(view_url)
            if officer.position.name in ['President','Vice President','Graduate Student Vice President']:
                self.assertEqual(resp.status_code,200)
            else:
                self.assertEqual(resp.status_code,302)
            client.logout()
        #admin should be able to access
        self.assertTrue(client.login(username=self.admin.username,password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code,200)
        context = resp.context
        self.assertTrue('formset' in context)
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'],'joining')
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'],'about')
        self.assertTrue('prefix' in context)
        self.assertEqual(context['prefix'],'joining')
        self.assertTrue('user' in context)
        self.assertEqual(context['user'],self.admin)
        self.assertFalse(context['can_add_row'])
        self.assertFalse(context['has_files'])
        self.assertTrue('base' in context)
        
        #test submissions, first one that succeeds
        marble = open('about/tests/test_photos/about_marbles.jpg','rb')
        pdf_file = open('about/tests/test_docs/test.pdf','rb')
        post_data = {
          'joining-TOTAL_FORMS':u'4',
          'joining-MAX_NUM_FORMS':u'',
          'joining-INITIAL_FORMS':u'4',
        }
        joining_sections =JoiningTextField.objects.all()
        for idx,sect in enumerate(joining_sections):
            post_data['joining-%d-id'%idx]=sect.id
            post_data['joining-%d-section'%idx]=sect.section
            post_data['joining-%d-text'%idx]=sect.text
        
        #change one
        post_data['joining-2-text']=u'Lorem Ipsum, Ipsum Factum'
        
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(len(resp.redirect_chain),1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1],302)
        self.assertTrue(reverse('about:eligibility') in med[0])
        self.assertEqual(resp.status_code,200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(JoiningTextField.objects.count(),4)
        #test submissions, missing the required fields
        post_data['joining-2-text']=u''
        post_data['joining-2-section']=u''
        resp = client.post(view_url,post_data,follow=True)
        self.assertEqual(resp.status_code,200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertFormsetError(resp,'formset',2,'section','This field is required.')
        self.assertFormsetError(resp,'formset',2,'text','This field is required.')
        client.logout()

    def test_officer_ajax(self):
        
        officers = Officer.objects.all()
        officers[2].term.clear()
        officers[2].term.add(AcademicTerm.objects.get(semester_type__name='Fall',year=2012))
        for officer in officers:
            view_url = reverse('about:officer',args=[officer.id])
            resp = self.client.get(view_url,HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(resp.status_code,200)
            if officer.position.name=='Advisor':
                self.assertFalse(unicode(officer.position) in resp.content,msg='%s name in response and should not be'%unicode(officer.position))
            else:
                self.assertTrue(unicode(officer.position) in resp.content,msg='%s name in response'%unicode(officer.position))
            self.assertTrue(unicode(officer.user.get_firstlast_name()) in resp.content,msg='%s user name not in response'%unicode(officer.position))
            if (AcademicTerm.get_current_term() in officer.term.all()) and not (officer.position.name=='Advisor'):
                self.assertTrue(officer.position.email in resp.content,msg='%s position email not in response'%unicode(officer.position))
                self.assertFalse(officer.user.get_email() in resp.content,msg='%s personal email in response for current term'%unicode(officer.position))
            else:
                self.assertFalse(officer.position.email in resp.content,msg='%s position email in response for non-current term or advisor'%unicode(officer.position))
                self.assertTrue(officer.user.get_email() in resp.content,msg='%s personal email not in response for past term or advisor'%unicode(officer.position))
        officers[2].term.clear()
        officers[2].term.add(AcademicTerm.get_current_term())