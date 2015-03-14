import datetime
import factory
import string
from math import ceil, pow

from django.contrib.auth.models import User
from django.utils.text import slugify

from mig_main.models import AcademicTerm, CurrentTerm, OfficerPosition,\
                    MemberProfile, UserProfile, Status, Standing, Major,\
                    TBPChapter, ShirtSize, OfficerTeam
from requirements.tests.factories import SemesterTypeFactory

OFFICER_POSITION_NAMES = ['President', 'Vice President',
                          'Graduate Student Vice President', 'Secretary',
                          'Treasurer', 'External Vice President',
                          'Corporate Relations Officer',
                          'Chapter Development Officer',
                          'Historian', 'Publicity Officer',
                          'Membership Officer', 'Website Chair',
                          'Service Coordinator', 'K-12 Outreach Officer',
                          'Campus Outreach Officer', 'Activities Officer',
                          'Campus Outreach Chair', 'Advisor', 'Apparel Chair',
                          'Alumni Relations Chair']

OFFICER_POSITION_TYPES = ['O', 'O', 'O', 'O', 'O', 'O',
                          'O', 'O', 'O', 'O', 'O', 'C',
                          'O', 'O', 'O', 'O', 'C', 'O',
                          'C', 'C']

NUM_OFFICERS = len(OFFICER_POSITION_NAMES)
MARBLES_PATH = 'migweb/test_photos/about_marbles.jpg'


def get_term(name, year):
    return AcademicTerm.objects.get(year=year, semester_type__name=name)


class AcademicTermFactory(factory.DjangoModelFactory):
    class Meta:
        model = AcademicTerm
    semester_type = factory.SubFactory(SemesterTypeFactory)
    year = factory.Iterator([2010, 2010, 2010, 2011, 2011, 2011,
                             2012, 2012, 2012, 2013, 2013, 2013,
                             2014, 2014, 2014, 2015, 2015, 2015])


class CurrentTermFactory(factory.DjangoModelFactory):
    class Meta:
        model = CurrentTerm
    current_term = factory.LazyAttribute(lambda o: get_term('Winter', 2015))


class OfficerPositionFactory(factory.DjangoModelFactory):
    class Meta:
        model = OfficerPosition
    name = factory.Iterator(OFFICER_POSITION_NAMES)
    description = 'words'
    email = factory.LazyAttribute(lambda o: slugify(unicode(o.name.lower())) +
                                  u'@umich.edu')
    enabled = True
    display_order = factory.Sequence(lambda n: n)
    position_type = factory.Iterator(OFFICER_POSITION_TYPES)


def get_user(o):
    return User.objects.create_user(o.uniqname,
                                    o.uniqname + '@umich.edu',
                                    'password')


class UserProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserProfile

    @factory.sequence
    def uniqname(n):
        power = 7
        uniq = ''
        for count in range(8):
            power = 7-count
            if n >= pow(26, power):
                remainder = n % pow(26, power)
                digit = int((n) / pow(26, power))
                uniq = uniq + string.ascii_lowercase[digit]
                n = remainder
            else:
                uniq = uniq + 'a'
        return uniq

    user = factory.LazyAttribute(lambda o: get_user(o))
    # Name Stuff
    first_name = 'John'
    last_name = 'Doe'


class MajorFactory(factory.DjangoModelFactory):
    class Meta:
        model = Major
    name = factory.Iterator(['Aerospace Engineering', 'Electrical Engineering',
                             'Computer Science'])
    acronym = factory.Iterator(['AERO', 'EE', 'CSE'])

    # probably not needed
    @factory.post_generation
    def standing(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for standing in extracted:
                self.standing.add(standing)


class StatusFactory (factory.DjangoModelFactory):
    class Meta:
        model = Status
    name = factory.Iterator(['Active', 'Electee', 'Non-Member'])


class StandingFactory (factory.DjangoModelFactory):
    class Meta:
        model = Standing
    name = factory.Iterator(['Undergraduate', 'Graduate', 'Alumni'])


class ShirtSizeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ShirtSize
    name = factory.Iterator(['Small', 'Medium', 'Large'])
    acronym = factory.Iterator(['S', 'M', 'L'])


class TBPChapterFactory(factory.DjangoModelFactory):
    class Meta:
        model = TBPChapter
    state = 'MI'
    letter = factory.Iterator(['A', 'B', 'G'])
    school = factory.Iterator(['MSU', 'Tech', 'UM'])


class MemberProfileFactory(UserProfileFactory):
    class Meta:
        model = MemberProfile
    status = factory.LazyAttribute(lambda o: Status.objects.get(name='Active'))
    UMID = factory.Sequence(lambda n: 10000000 + n)
    init_chapter = factory.LazyAttribute(lambda o:
                                         TBPChapter.objects.get(state='MI',
                                                                letter='G'))
    standing = factory.LazyAttribute(lambda o:
                                     Standing.objects.get(name='Undergraduate')
                                     )
    shirt_size = factory.LazyAttribute(lambda o:
                                       ShirtSize.objects.get(acronym='M'))
    short_bio = 'Can Haz Bio'
    init_term = factory.LazyAttribute(lambda o: get_term('Winter', 2014))
    expect_grad_date = datetime.date(year=2016, month=1, day=5)
    photo = factory.django.ImageField(from_path=MARBLES_PATH)
    phone = '555-555-5555'

    # probably not needed
    @factory.post_generation
    def major(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for major in extracted:
                self.major.add(major)


def get_lead(team):
    if team.name == 'Executive Committee':
        return OfficerPosition.objects.get(name='President')
    elif team.name == 'PD':
        return OfficerPosition.objects.get(name='Corporate Relations Officer')
    elif team.name == 'Events':
        return OfficerPosition.objects.get(name='Service Coordinator')
    elif team.name == 'Chapter':
        return OfficerPosition.objects.get(name='Chapter Development Officer')
    else:
        return None


class OfficerTeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = OfficerTeam
    name = factory.Iterator(['Executive Committee', 'PD', 'Events', 'Chapter'])
    lead = factory.LazyAttribute(lambda o: get_lead(o))
    start_term = factory.LazyAttribute(lambda o: get_term('Fall', 2013))
    end_term = None

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for member in extracted:
                self.members.add(member)
        else:
            if self.name == 'Executive Committee':
                self.members.add(OfficerPosition.objects.get(name='President'))
                self.members.add(OfficerPosition.objects.get(name='Vice President'))
                self.members.add(OfficerPosition.objects.get(name='Graduate Student Vice President'))
                self.members.add(OfficerPosition.objects.get(name='Secretary'))
                self.members.add(OfficerPosition.objects.get(name='Treasurer'))
            elif self.name == 'PD':
                self.members.add(OfficerPosition.objects.get(name='Corporate Relations Officer'))
                self.members.add(OfficerPosition.objects.get(name='External Vice President'))
            elif self.name == 'Events':
                self.members.add(OfficerPosition.objects.get(name='Service Coordinator'))
                self.members.add(OfficerPosition.objects.get(name='K-12 Outreach Officer'))
                self.members.add(OfficerPosition.objects.get(name='Campus Outreach Officer'))
                self.members.add(OfficerPosition.objects.get(name='Campus Outreach Chair'))
                self.members.add(OfficerPosition.objects.get(name='Activities Officer'))
            elif self.name == 'Events':
                self.members.add(OfficerPosition.objects.get(name='Chapter Development Officer'))
                self.members.add(OfficerPosition.objects.get(name='Membership Officer'))
                self.members.add(OfficerPosition.objects.get(name='Historian'))
                self.members.add(OfficerPosition.objects.get(name='Publicity Officer'))
                self.members.add(OfficerPosition.objects.get(name='Website Chair'))
                self.members.add(OfficerPosition.objects.get(name='Alumni Relations Chair'))
                self.members.add(OfficerPosition.objects.get(name='Apparel Chair'))
