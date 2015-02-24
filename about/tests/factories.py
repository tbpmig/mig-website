import datetime
import factory
import string

from math import ceil,pow
from django.contrib.auth.models import User
from django.core.files import File
from django.utils.text import slugify

from about.models import *
from history.models import Officer,GoverningDocument,GoverningDocumentType
from mig_main.models import AcademicTerm,CurrentTerm,OfficerPosition,MemberProfile,UserProfile,Status,Standing,Major,TBPChapter,ShirtSize,OfficerTeam
from requirements.models import SemesterType

JOINING_TEXT=r'''A First Level Header
====================

A Second Level Header
---------------------

Now is the time for all good men to come to
the aid of their country. This is just a
regular paragraph.

The quick brown fox jumped over the lazy
dog's back.

### Header 3

> This is a blockquote.
> 
> This is the second paragraph in the blockquote.
>
> ## This is an H2 in a blockquote'''

OFFICER_POSITION_NAMES=['President','Vice President','Graduate Student Vice President', 'Secretary',
                        'Treasurer','External Vice President','Corporate Relations Officer','Chapter Development Officer',
                        'Historian','Publicity Officer','Membership Officer','Website Chair','Service Coordinator','K-12 Outreach Officer',
                        'Campus Outreach Officer','Activities Officer','Campus Outreach Chair','Advisor','Apparel Chair','Alumni Relations Chair']

OFFICER_POSITION_TYPES=['O','O', 'O','O','O','O','O','O','O','O','O','C','O','O','O','O','C','O','C','C']    

NUM_OFFICERS = len(OFFICER_POSITION_NAMES)                 
class SemesterTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = SemesterType
    name=factory.Iterator(['Winter','Summer','Fall'])

class AcademicTermFactory(factory.DjangoModelFactory):
    class Meta:
        model = AcademicTerm
    semester_type=factory.SubFactory(SemesterTypeFactory)
    year =factory.Iterator([2010,2010,2010,2011,2011,2011,2012,2012,2012,2013,2013,2013,2014,2014,2014,2015,2015,2015])

class CurrentTermFactory(factory.DjangoModelFactory):
    class Meta:
        model = CurrentTerm
    current_term = factory.LazyAttribute(lambda o:AcademicTerm.objects.get(year=2015,semester_type__name='Winter'))
class AboutPhotoFactory(factory.DjangoModelFactory):
    class Meta:
        model = AboutSlideShowPhoto
    title = factory.Iterator(['Marbles','Flower'])
    text = factory.Iterator(['marbles','flower'])
    link = ''
    active = factory.Iterator([True,False])
    photo = factory.django.ImageField(from_path='about/tests/test_photos/about_marbles.jpg')
    
class OfficerPositionFactory(factory.DjangoModelFactory):
    class Meta:
        model = OfficerPosition
    name            = factory.Iterator(OFFICER_POSITION_NAMES)
    description     = 'words'
    email           = factory.LazyAttribute(lambda o: slugify(unicode(o.name.lower()))+u'@umich.edu')
    enabled         = True
    display_order   = factory.Sequence(lambda n:n)
    position_type   = factory.Iterator(OFFICER_POSITION_TYPES)
   
class UserProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserProfile
    @factory.sequence
    def uniqname(n):
        power = 7
        uniq=''
        for count in range(8):
            power =7-count
            if n>=pow(26,power):
                remainder = n%pow(26,power)
                digit = int((n)/pow(26,power))
                uniq=uniq+string.ascii_lowercase[digit]
                n=remainder
            else:
                uniq=uniq+'a'
        return uniq
    #uniqname=factory.fuzzy.FuzzyText(length=8,chars='abcdefghijklmnopqrstuvwxyz')
    user = factory.LazyAttribute(lambda o: User.objects.create_user(o.uniqname,o.uniqname+'@umich.edu','password'))

    #Name Stuff
    first_name      = 'John'
    last_name       = 'Doe'

class MajorFactory(factory.DjangoModelFactory):
    class Meta:
        model = Major
    name = factory.Iterator(['Aerospace Engineering','Electrical Engineering','Computer Science'])
    acronym= factory.Iterator(['AERO','EE','CSE'])
    #probably not needed
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
    name = factory.Iterator(['Active','Electee','Non-Member'])
    
class StandingFactory (factory.DjangoModelFactory):
    class Meta:
        model = Standing
    name = factory.Iterator(['Undergraduate','Graduate','Alumni'])   

class ShirtSizeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ShirtSize
    name = factory.Iterator(['Small','Medium','Large']) 
    acronym = factory.Iterator(['S','M','L'])
    
class TBPChapterFactory(factory.DjangoModelFactory):
    class Meta:
        model = TBPChapter
    state = 'MI'
    letter = factory.Iterator(['A','B','G'])
    school = factory.Iterator(['MSU','Tech','UM'])
class MemberProfileFactory(UserProfileFactory):
    class Meta:
        model = MemberProfile
    status          = factory.LazyAttribute(lambda o:Status.objects.get(name='Active'))
    UMID            = factory.Sequence(lambda n: 10000000+n)
    init_chapter    = factory.LazyAttribute(lambda o:TBPChapter.objects.get(state='MI',letter='G'))
    standing        = factory.LazyAttribute(lambda o:Standing.objects.get(name='Undergraduate'))
    shirt_size      = factory.LazyAttribute(lambda o:ShirtSize.objects.get(acronym='M'))
    short_bio       = 'Can Haz Bio'
    init_term       = factory.LazyAttribute(lambda o:AcademicTerm.objects.get(year=2014,semester_type__name='Winter'))
    expect_grad_date= datetime.date(year=2016,month=1,day=5)
    
    #Uncomment this on actual server with Python Image Library installed
    photo   = factory.django.ImageField(from_path='about/tests/test_photos/about_marbles.jpg')
    phone           = '555-555-5555'
    #probably not needed
    @factory.post_generation
    def major(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for major in extracted:
                self.major.add(major)
class OfficerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Officer
    user            = factory.SubFactory(MemberProfileFactory)   
    position        = factory.SubFactory(OfficerPositionFactory)
    website_bio     = 'I have a bio'
    website_photo   = factory.django.ImageField(from_path='about/tests/test_photos/about_flower.jpg')
    
    @factory.post_generation
    def term(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for term in extracted:
                self.term.add(term)
        else:
            self.term.add(AcademicTerm.get_current_term())
class DocumentTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocumentType
    name = factory.Iterator(['Constitution','Bylaws'])
class OldDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocument
    id = factory.Sequence(lambda n:n)
    document_type = factory.LazyAttribute(lambda o:GoverningDocumentType.objects.get(name='Constitution') if o.id %2 else GoverningDocumentType.objects.get(name='Bylaws'))
    active = False
    pdf_file = factory.django.FileField(from_path='about/tests/test_docs/test.pdf')
class CurrentDocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = GoverningDocument
    id = factory.Sequence(lambda n:n)
    document_type = factory.LazyAttribute(lambda o:GoverningDocumentType.objects.get(name='Constitution') if o.id %2 else GoverningDocumentType.objects.get(name='Bylaws'))
    active = True
    pdf_file = factory.django.FileField(from_path='about/tests/test_docs/test.pdf')

class JoiningTextFactory(factory.DjangoModelFactory):
    class Meta:
        model = JoiningTextField
    section=factory.Iterator(['EL','Y','UG','GR'])
    text = JOINING_TEXT
 
def get_lead(team):
    if team.name == 'Executive Committee':
        return OfficerPosition.objects.get(name='President')
    elif team.name =='PD':
        return OfficerPosition.objects.get(name='Corporate Relations Officer')
    elif team.name =='Events':
        return OfficerPosition.objects.get(name='Service Coordinator')
    elif team.name =='Chapter':
        return OfficerPosition.objects.get(name='Chapter Development Officer')
    else:
        return None
class OfficerTeamFactory(factory.DjangoModelFactory):
    class Meta:
        model = OfficerTeam
    name = factory.Iterator(['Executive Committee','PD','Events','Chapter'])
    lead = factory.LazyAttribute(lambda o: get_lead(o))
    start_term = factory.LazyAttribute(lambda o:AcademicTerm.objects.get(year=2013,semester_type__name='Fall'))
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
            if self.name=='Executive Committee':
                self.members.add(OfficerPosition.objects.get(name='President'))
                self.members.add(OfficerPosition.objects.get(name='Vice President'))
                self.members.add(OfficerPosition.objects.get(name='Graduate Student Vice President'))
                self.members.add(OfficerPosition.objects.get(name='Secretary'))
                self.members.add(OfficerPosition.objects.get(name='Treasurer'))
            elif self.name =='PD':
                self.members.add(OfficerPosition.objects.get(name='Corporate Relations Officer'))
                self.members.add(OfficerPosition.objects.get(name='External Vice President'))
            elif self.name =='Events':
                self.members.add(OfficerPosition.objects.get(name='Service Coordinator'))
                self.members.add(OfficerPosition.objects.get(name='K-12 Outreach Officer'))
                self.members.add(OfficerPosition.objects.get(name='Campus Outreach Officer'))
                self.members.add(OfficerPosition.objects.get(name='Campus Outreach Chair'))
                self.members.add(OfficerPosition.objects.get(name='Activities Officer'))
            elif self.name =='Events':
                self.members.add(OfficerPosition.objects.get(name='Chapter Development Officer'))
                self.members.add(OfficerPosition.objects.get(name='Membership Officer'))
                self.members.add(OfficerPosition.objects.get(name='Historian'))
                self.members.add(OfficerPosition.objects.get(name='Publicity Officer'))
                self.members.add(OfficerPosition.objects.get(name='Website Chair'))
                self.members.add(OfficerPosition.objects.get(name='Alumni Relations Chair'))
                self.members.add(OfficerPosition.objects.get(name='Apparel Chair'))