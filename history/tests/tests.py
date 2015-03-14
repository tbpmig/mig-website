"""
This contains the tests (unit and integration) for the history module.

It currently contains:

"""
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from mig_main.tests.factories import AcademicTermFactory, TBPChapterFactory,\
                            StandingFactory, StatusFactory, MajorFactory,\
                            ShirtSizeFactory, CurrentTermFactory, NUM_OFFICERS
from history.tests.factories import OfficerFactory
from history.models import Officer
from mig_main.models import AcademicTerm, OfficerPosition, MemberProfile, Status
from mig_main.models import ShirtSize, TBPChapter, Major, Standing
from migweb.test_tools import MyClient


def setUpModule():
    print 'setting up about test data...'
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


def tearDownModule():
    """This should clear the database back to empty,
    only those objects created in the setup method need to be deleted. I think
    """
    print 'tearing down about module...'
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


class HistoryViewsTestCase(TestCase):

    def setUp(self):
        self.client = MyClient()
        self.user = User.objects.get(username='johndoe')
        self.admin = User.objects.get(username='jimharb')

    def tearDown(self):
        del(self.client)

    def test_views_index(self):
        pass
