"""
This contains the tests (unit and integration) for the corporate module.

It currently contains:

"""
from os.path import isfile

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from corporate.models import CorporateTextField
from corporate.tests.factories import CorporateTextFactory,\
                            CorporateResourceGuideFactory
from mig_main.tests.factories import AcademicTermFactory, TBPChapterFactory,\
                            StandingFactory, StatusFactory, MajorFactory,\
                            ShirtSizeFactory, CurrentTermFactory, NUM_OFFICERS
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
        pass

    def test_views_update_resource_guide(self):
        pass
