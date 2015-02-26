"""
This contains the tests (unit and integration) for the corporate module.

It currently contains:

"""
from os.path import isfile

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.files import File
from django.template.defaultfilters import slugify

from corporate.auxiliary_scripts import compile_resumes, update_resume_zips  
from corporate.auxiliary_scripts import RESUMES_BY_MAJOR_LOCATION
from corporate.auxiliary_scripts import RESUMES_BY_YEAR_LOCATION 
from corporate.models import CorporateTextField, CorporateResourceGuide
from corporate.tests.factories import CorporateTextFactory,\
                            CorporateResourceGuideFactory
from mig_main.tests.factories import AcademicTermFactory, TBPChapterFactory,\
                        StandingFactory, StatusFactory, MajorFactory,\
                        ShirtSizeFactory, CurrentTermFactory, NUM_OFFICERS,\
                        UserProfileFactory, MemberProfileFactory
from history.tests.factories import OfficerFactory
from history.models import Officer
from mig_main.models import AcademicTerm, OfficerPosition, MemberProfile
from mig_main.models import ShirtSize, TBPChapter, Major, Standing, Status
from migweb.test_tools import MyClient

CAN_EDIT_CORP = ['President', 'Corporate Relations Officer',
                 'External Vice President']

CORPORATE_HTML = r'''<h1>A First Level Header</h1>
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
    print 'setting up corporate test data...'
    AcademicTermFactory.create_batch(18)
    TBPChapterFactory.create_batch(3)
    StandingFactory.create_batch(3)
    StatusFactory.create_batch(3)
    MajorFactory.create_batch(3)
    ShirtSizeFactory.create_batch(3)
    CurrentTermFactory()
    OfficerFactory.create_batch(NUM_OFFICERS)
    User.objects.create_user('johndoe', 'johndoe@umich.edu', 'password')
    User.objects.create_superuser('jimharb', 'jimharb@umich.edu', 'password')
    CorporateTextFactory.create_batch(2)


def tearDownModule():
    """This should clear the database back to empty,
    only those objects created in the setup method need to be deleted. I think
    """
    print '\ntearing down corporate module...'
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
    CorporateTextField.objects.all().delete()
    print 'teardown complete.'


class CorporateViewsTestCase(TestCase):

    def setUp(self):
        self.client = MyClient()
        self.user = User.objects.get(username='johndoe')
        self.admin = User.objects.get(username='jimharb')

    def tearDown(self):
        del(self.client)

    def test_views_index(self):
        corp_text = CorporateTextField.objects.all().order_by('-section')
        view_url = reverse('corporate:index')
        update_corp_url = reverse('corporate:update_corporate_page')
        update_resource_url = reverse('corporate:update_resource_guide')
        client = self.client
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context

        # Test that the context is correct-common items
        self.assertTrue('can_edit_corporate' in context)
        self.assertFalse(context['can_edit_corporate'])
        self.assertTrue('contact_text' in context)
        self.assertEqual(context['contact_text'].count(), 1)
        self.assertEqual(context['contact_text'][0], corp_text[1])
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'], 'corporate')

        # specific items
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'], 'index')
        self.assertTrue('involvement_text' in context)
        self.assertEqual(resp.content.count(CORPORATE_HTML), 2,
                         msg='Markdown not working correctly')

        # test non-admin persmissions
        login = client.login(username=self.user.username,
                             password='password')

        self.assertTrue(login)
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('can_edit_corporate' in context)
        self.assertFalse(context['can_edit_corporate'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.user)
        self.assertFalse(update_corp_url in resp.content)
        self.assertFalse(update_resource_url in resp.content)
        client.logout()

        # Test admin permissions
        self.assertTrue(client.login(username=self.admin.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('can_edit_corporate' in context)
        self.assertTrue(context['can_edit_corporate'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.admin)
        self.assertTrue(update_corp_url in resp.content)
        self.assertTrue(update_resource_url in resp.content)
        client.logout()

        # test officer permissions
        for officer in Officer.objects.all():
            self.assertTrue(client.login(username=officer.user.user.username,
                                         password='password'))
            resp = client.get(view_url)
            self.assertEqual(resp.status_code, 200)
            context = resp.context
            self.assertTrue('can_edit_corporate' in context)
            if officer.position.name in CAN_EDIT_CORP:
                self.assertTrue(context['can_edit_corporate'])
                self.assertTrue(update_corp_url in resp.content)
                self.assertTrue(update_resource_url in resp.content)
            else:
                self.assertFalse(context['can_edit_corporate'])
                self.assertFalse(update_corp_url in resp.content)
                self.assertFalse(update_resource_url in resp.content)
            self.assertTrue('user' in context)
            self.assertEqual(context['user'], officer.user.user)
            client.logout()

    def test_views_resumes(self):
        corp_text = CorporateTextField.objects.all().order_by('-section')
        view_url = reverse('corporate:resumes')
        update_corp_url = reverse('corporate:update_corporate_page')
        update_resource_url = reverse('corporate:update_resource_guide')
        client = self.client
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context

        # Test that the context is correct-common items
        self.assertTrue('can_edit_corporate' in context)
        self.assertFalse(context['can_edit_corporate'])
        self.assertTrue('contact_text' in context)
        self.assertEqual(context['contact_text'].count(), 1)
        self.assertEqual(context['contact_text'][0], corp_text[1])
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'], 'corporate')

        # specific items
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'], 'resumes')
        self.assertTrue('by_major_zip' in context)
        self.assertTrue('by_year_zip' in context)
        self.assertTrue(isfile('migweb/media/' + context['by_major_zip']))
        self.assertTrue(isfile('migweb/media/' + context['by_year_zip']))
        self.assertEqual(resp.content.count(CORPORATE_HTML), 1,
                         msg='Markdown not working correctly')

        # test non-admin persmissions
        login = client.login(username=self.user.username,
                             password='password')

        self.assertTrue(login)
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('can_edit_corporate' in context)
        self.assertFalse(context['can_edit_corporate'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.user)
        self.assertFalse(update_corp_url in resp.content)
        self.assertFalse(update_resource_url in resp.content)
        client.logout()

        # Test admin permissions
        self.assertTrue(client.login(username=self.admin.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('can_edit_corporate' in context)
        self.assertTrue(context['can_edit_corporate'])
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.admin)
        self.assertTrue(update_corp_url in resp.content)
        self.assertTrue(update_resource_url in resp.content)
        client.logout()

        # test officer permissions
        for officer in Officer.objects.all():
            self.assertTrue(client.login(username=officer.user.user.username,
                                         password='password'))
            resp = client.get(view_url)
            self.assertEqual(resp.status_code, 200)
            context = resp.context
            self.assertTrue('can_edit_corporate' in context)
            if officer.position.name in CAN_EDIT_CORP:
                self.assertTrue(context['can_edit_corporate'])
                self.assertTrue(update_corp_url in resp.content)
                self.assertTrue(update_resource_url in resp.content)
            else:
                self.assertFalse(context['can_edit_corporate'])
                self.assertFalse(update_corp_url in resp.content)
                self.assertFalse(update_resource_url in resp.content)
            self.assertTrue('user' in context)
            self.assertEqual(context['user'], officer.user.user)
            client.logout()

    def test_views_update_corporate(self):
        view_url = reverse('corporate:update_corporate_page')
        client = self.client
        resp = self.client.get(view_url, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertTrue(resp.context['error_message'])
        # no one without a profile should have access
        self.assertTrue(client.login(username=self.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # no non-member should be able to access
        generic_user = UserProfileFactory()
        self.assertTrue(client.login(username=generic_user.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # no general member should be able to access
        generic_member = MemberProfileFactory()
        self.assertTrue(client.login(username=generic_member.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # only a few officers can access it
        officers = Officer.objects.all()
        for officer in officers:
            self.assertTrue(client.login(username=officer.user.user.username,
                                         password='password'))
            resp = client.get(view_url)
            if officer.position.name in CAN_EDIT_CORP:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 302)
            client.logout()
        # admin should be able to access
        self.assertTrue(client.login(username=self.admin.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('formset' in context)
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'], 'index')
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'], 'corporate')
        self.assertTrue('prefix' in context)
        self.assertEqual(context['prefix'], 'corporate_page')
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.admin)
        self.assertFalse(context['can_add_row'])
        self.assertFalse(context['has_files'])
        self.assertTrue('base' in context)

        # test submissions, first one that succeeds
        post_data = {
          'corporate_page-TOTAL_FORMS': u'3',
          'corporate_page-MAX_NUM_FORMS': u'',
          'corporate_page-INITIAL_FORMS': u'2',
        }
        corp_sections = CorporateTextField.objects.all()
        for idx, sect in enumerate(corp_sections):
            post_data['corporate_page-%d-id' % idx] = sect.id
            post_data['corporate_page-%d-section' % idx] = sect.section
            post_data['corporate_page-%d-text' % idx] = sect.text

        # there is one blank one
        post_data['corporate_page-%d-id' % 2] = u''
        post_data['corporate_page-%d-section' % 2] = u'OP'
        post_data['corporate_page-%d-text' % 2] = u''
        # change one
        post_data['corporate_page-1-text'] = u'Lorem Ipsum, Ipsum Factum'
        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(CorporateTextField.objects.count(), 2)
        # test submissions, missing the required fields
        post_data['corporate_page-2-text'] = u'a'
        post_data['corporate_page-2-section'] = u''
        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertFormsetError(resp, 'formset', 2, 'section',
                                'This field is required.')
        
        # add a new one and reset the other
        post_data['corporate_page-1-text'] = post_data['corporate_page-0-text']
        post_data['corporate_page-2-text'] = u'nothing'
        post_data['corporate_page-2-section'] = u'OT'
        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(CorporateTextField.objects.count(), 3)
        client.logout()

    def test_views_update_resource_guide(self):
        view_url = reverse('corporate:update_resource_guide')
        client = self.client
        resp = self.client.get(view_url, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertTrue(resp.context['error_message'])
        # no one without a profile should have access
        self.assertTrue(client.login(username=self.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # no non-member should be able to access
        generic_user = UserProfileFactory()
        self.assertTrue(client.login(username=generic_user.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # no general member should be able to access
        generic_member = MemberProfileFactory()
        self.assertTrue(client.login(username=generic_member.user.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 302)
        client.logout()
        # only a few officers can access it
        officers = Officer.objects.all()
        for officer in officers:
            self.assertTrue(client.login(username=officer.user.user.username,
                                         password='password'))
            resp = client.get(view_url)
            if officer.position.name in CAN_EDIT_CORP:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 302)
            client.logout()
        # admin should be able to access
        self.assertTrue(client.login(username=self.admin.username,
                                     password='password'))
        resp = client.get(view_url)
        self.assertEqual(resp.status_code, 200)
        context = resp.context
        self.assertTrue('form' in context)
        self.assertTrue('subnav' in context)
        self.assertEqual(context['subnav'], 'index')
        self.assertTrue('main_nav' in context)
        self.assertEqual(context['main_nav'], 'corporate')
        self.assertTrue('user' in context)
        self.assertEqual(context['user'], self.admin)
        self.assertTrue(context['has_files'])
        self.assertTrue('base' in context)

        # test submissions, first one that succeeds
        pdf_file = open('migweb/test_docs/test.pdf', 'rb')
        post_data = {
          'name': u'resource_guide_initial',
          'resource_guide': pdf_file,
        }

        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(CorporateResourceGuide.objects.count(), 1)
        self.assertEqual(CorporateResourceGuide.objects.filter(active=True).count(), 1)
        self.assertEqual(CorporateResourceGuide.objects.filter(active=False).count(), 0)
        # test submissions, missing the required fields
        post_data['name'] = u'empty'
        post_data['resource_guide'] = u''
        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['error_message'])
        self.assertFalse(resp.context['success_message'])
        self.assertFormError(resp, 'form', 'resource_guide',
                                'This field is required.')
        
        # add a new one
        post_data['name'] = u'resource_guide_2'
        pdf_file = open('migweb/test_docs/test.pdf', 'rb')
        post_data['resource_guide'] = pdf_file
        resp = client.post(view_url, post_data, follow=True)
        self.assertEqual(len(resp.redirect_chain), 1)
        for med in resp.redirect_chain:
            self.assertEqual(med[1], 302)
        self.assertTrue(reverse('corporate:index') in med[0])
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['error_message'])
        self.assertFalse(resp.context['warning_message'])
        self.assertTrue(resp.context['success_message'])
        self.assertEqual(CorporateTextField.objects.count(), 2)
        self.assertEqual(CorporateResourceGuide.objects.filter(active=True).count(), 1)
        self.assertEqual(CorporateResourceGuide.objects.filter(active=False).count(), 1)
        self.assertEqual(CorporateResourceGuide.objects.get(active=True).name,
                         'resource_guide_2')
        client.logout()


class CorporateAuxiliaryTestCase(TestCase):
    def setUp(self):
        pdf_file = File(open('migweb/test_docs/test.pdf', 'rb'))
        profiles =MemberProfile.objects.all()
        majors = Major.objects.all().order_by('id')
        for idx, profile in enumerate(profiles):
            resume_name=slugify(profile.last_name+'_'+profile.first_name+'_'+profile.uniqname)+'.pdf'
            profile.resume.save(resume_name, pdf_file)
            # now give them majors
            profile.major.add(majors[idx % majors.count()])
            profile.save()
    def tearDown(self):
        pass

    def test_resume_compile(self):
        compile_resumes()
    def test_update_zips(self):
        pass