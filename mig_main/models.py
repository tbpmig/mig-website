from django.contrib.auth.models import User
from django.core.validators import validate_email, RegexValidator,MinValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.text import slugify
from localflavor.us.models import PhoneNumberField
from stdimage import StdImageField
from mig_main.pdf_field import ContentTypeRestrictedFileField,pdf_types

def get_actives():
    query = models.Q(status__name='Active')
    return MemberProfile.objects.filter(query)

def get_electees():
    query = models.Q(status__name='Electee',still_electing=True)
    return MemberProfile.objects.filter(query)

def get_members():
    query = models.Q(status__name='Active')|models.Q(status__name='Electee',still_electing=True)
    return MemberProfile.objects.filter(query)

def resume_file_name(instance,filename):
    return '/'.join([u"resumes",instance.uniqname+u'.pdf'])
#need table of project leaders...probably a permissions group
PREFERENCES = [
        {
            'name':'google_calendar_add',
            'values':('always','never'),
            'verbose':'Do you want to add events signed up for to your personal calendar?',
            'default':'never',
        },
        {
            'name':'google_calendar_account',
            'values':('umich','alternate'),
            'verbose':'Which email has your personal calendar',
            'default':'umich',
        },
]

# homepage models
class SlideShowPhoto(models.Model):
    photo   = StdImageField(upload_to='home_page_photos',thumbnail_size=(1050,790))
    active  = models.BooleanField()
    title   = models.TextField()
    text    = models.TextField()
    link    = models.CharField(max_length=256)

# general usage models
class AcademicTerm(models.Model):
    year            = models.PositiveSmallIntegerField(validators = [MinValueValidator(1960)])
    semester_type   = models.ForeignKey('requirements.SemesterType')
    
    def get_abbreviation(self):
        return self.semester_type.name[0]+str(self.year)
    def __unicode__(self):
        return self.semester_type.name +' '+unicode(self.year)
    def __gt__(self,term2):
        if not hasattr(term2,'year'):
            return True
        if self.year > term2.year:
            return True
        if self.year < term2.year:
            return False
        return self.semester_type > term2.semester_type
    def __lt__(self,term2):
        if not hasattr(term2,'year'):
            return False
        if self.year < term2.year:
            return True
        if self.year > term2.year:
            return False
        return self.semester_type < term2.semester_type
    def __eq__(self,term2):
        if not hasattr(term2,'year'):
            return False
        if self.year != term2.year:
            return False
        return self.semester_type == term2.semester_type
    def __ne__(self,term2):
        return not self == term2
    def __le__(self,term2):
        return not self > term2
    def __ge__(self,term2):
        return not self < term2

class CurrentTerm(models.Model):
    current_term = models.ForeignKey(AcademicTerm)
    def __unicode__(self):
        return unicode(self.current_term)

class TBPChapter(models.Model):
    class Meta:
        verbose_name = 'TBP Chapter'
        verbose_name_plural = 'TBP Chapters'
    state   = models.CharField(max_length=2,validators=[RegexValidator(regex=r'^[A-Z]{2}$',
                                                                message="Must be the state (or territory) 2-letter code MI")])
    letter  = models.CharField(max_length=4,validators=[RegexValidator(regex=r'^[A-I,K-U,W-Z]+$',
                                                                message="Greek letter (latin equivalent), e.g. Gamma is G, Theta is Q")])
    school  = models.CharField(max_length = 70) 
    def __unicode__(self):
        return self.state+'-'+self.letter
class OfficerPosition(models.Model):
        
    name            = models.CharField(max_length = 45)
    description     = models.TextField()
    email           = models.EmailField(max_length=254)
    enabled         = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name

class OfficerTeam(models.Model):
    name    = models.CharField(max_length=80)
    lead    = models.ForeignKey(OfficerPosition,related_name='team_lead')
    members = models.ManyToManyField(OfficerPosition,related_name='members')
    start_term = models.ForeignKey(AcademicTerm,related_name='teams_starting_in_term') 
    end_term = models.ForeignKey(AcademicTerm,related_name='teams_ending_in_term',null=True,blank=True) 
    def __unicode__(self):
        return self.name
        
class Standing(models.Model):
    name        = models.CharField(max_length = 20)
    enabled     = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
    
class Major(models.Model):
    name            = models.CharField(max_length=60)
    acronym         = models.CharField(max_length=10)
    standing_type   = models.ManyToManyField(Standing)
    enabled         = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name+' ('+self.acronym+')'
    
class Status(models.Model):
    class Meta:
        verbose_name_plural = 'Statuses'
    name        = models.CharField(max_length = 20)
    enabled     = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name
    
class ShirtSize(models.Model):
    name    = models.CharField(max_length = 35)
    acronym = models.CharField(max_length=4)
    enabled = models.BooleanField(default=True)
    def __unicode__(self):
        return self.name

    
MAX_ADV_TERM = 3

class UserPreference(models.Model):
    user = models.ForeignKey('mig_main.UserProfile')
    preference_type = models.CharField(max_length=64)
    preference_value= models.CharField(max_length=64)
    def __unicode__(self):
        return unicode(self.user)+': '+self.preference_type

#NOTES:
    #Some of the choices should be populated elsewhere, but for the time being are here
    #Currently doesn't have photo field, needs Python Image Library for that
        #Couldn't install it locally, should be easier on server
    #Progress is still not noted at all
    #Committees and awards are both unhandled at this point
class UserProfile(models.Model):
    
    user = models.OneToOneField(User,on_delete=models.PROTECT)

    #Name Stuff
    nickname        = models.CharField(max_length=40,blank=True)
    first_name      = models.CharField(max_length=40)
    middle_name     = models.CharField(max_length=40,blank=True)
    last_name       = models.CharField(max_length=40)
    suffix          = models.CharField(max_length=15,blank=True)
    title           = models.CharField(max_length=20,blank=True)
    uniqname        = models.CharField(max_length=8,primary_key=True,
                                       validators=[RegexValidator(regex=r'^[a-z]{3,8}$',
                                       message="Your uniqname must be 3-8 characters, all lowercase.")
                                        ])
    #Methods
    def get_full_name(self):
        name = self.title+" " if self.title else ""
        name = name + self.first_name + " "
        name = name + self.middle_name+" " if self.middle_name else name
        name = name + self.last_name
        name = name + ", "+self.suffix if self.suffix else name
        return name
    def __unicode__(self):
        return self.get_full_name()+" ("+self.uniqname+")"
    
    def get_casual_name(self):
        if len(self.nickname)>0:
            return self.nickname
        else:
            return self.first_name
    def get_firstlast_name(self):
        first_name = self.get_casual_name()
        if first_name == self.last_name:
            first_name = self.first_name
        return first_name+' '+self.last_name

    def get_email(self):
        return self.uniqname+"@umich.edu"
    
    def is_member(self):
        try:
            self.memberprofile
            return True
        except ObjectDoesNotExist:
            return False

class MemberProfile(UserProfile):
    
    
    #Alumni Mail Frequency Options
    ALUM_MAIL_FREQ_CHOICES = (
        ("NO", "None"),
        ("YR", "Yearly"),
        ("SM",  "Semesterly"),
        ("MO",  "Monthly"),
        ("WK",  "Weekly (left on tbp.all)"),
    )
    
    #Preferred Email address
    MAIL_PREF_CHOICES = (
        ("UM", "Umich email"),
        ("ALT", "Alternate email"),
    )
    
    
    #Gender Choices
    GENDER_CHOICES = (
        ("F", "Female"),
        ("M", "Male"),
        ("O", "Other/Prefer not to respond"),
    )
    
    #Actual Fields
    #Name Stuff
    
    
    #Classifications
    major           = models.ManyToManyField(Major)
                                        
    status          = models.ForeignKey(Status,on_delete=models.PROTECT)
                                    
    UMID            = models.CharField(max_length=8,
                                       validators=[RegexValidator(regex=r'^[0-9]{8}$',
                                                                message="Your UMID must be 8 numbers.")
                                        ])
    init_chapter    = models.ForeignKey(TBPChapter,on_delete=models.PROTECT,verbose_name="Initiating Chapter")
    
    
    
    standing        = models.ForeignKey(Standing,on_delete=models.PROTECT)
                                        
    alt_email       = models.EmailField("Alternate email",max_length=254,blank=True)

    jobs_email      = models.BooleanField("Receive corporate emails?",default=True)
    
    alum_mail_freq  = models.CharField("How frequently would you like alumni emails?", 
                                        max_length=2,
                                        choices=ALUM_MAIL_FREQ_CHOICES,
                                        default="WK")
    job_field       = models.CharField("What is your job field?",max_length=50,
                                        blank=True)#Only for alums
                                        
    employer        = models.CharField("Your employer",max_length=60,
                                        blank=True)#Only for alums
    preferred_email = models.CharField(max_length=3,
                                        choices=MAIL_PREF_CHOICES,
                                        default="UM")
    meeting_speak   = models.BooleanField("Are you interested in speaking at a meeting?",default=False)    #Willingness to speak at a meeting/event

    edu_bckgrd_form = ContentTypeRestrictedFileField(
        upload_to='grad_background_forms',
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=True,
        verbose_name="Educational Background Form (Grad Electees only)",
    )#File of this, grad electees only
    shirt_size      = models.ForeignKey(ShirtSize,on_delete=models.PROTECT)
    short_bio       = models.TextField()
    init_term       = models.ForeignKey(AcademicTerm, on_delete=models.PROTECT,verbose_name="Initiation term")
    gender          = models.CharField(max_length=1,
                                        choices=GENDER_CHOICES,
                                        default="O")
    expect_grad_date= models.DateField("Expected graduation date")
    still_electing  = models.BooleanField(default=True)
    
    #Uncomment this on actual server with Python Image Library installed
    photo   = StdImageField(upload_to='member_photos',thumbnail_size=(555,775))
    resume          = ContentTypeRestrictedFileField(
        upload_to=resume_file_name,
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=True
    )
    phone           = PhoneNumberField()
    
    
    #Methods
    def get_num_terms_distinction(self,distinction):
        distinctions = self.distinction_set.filter(distinction_type = distinction)
        return distinctions.count()
    def get_email(self):
        if self.preferred_email=="UM" or not self.alt_email:
            return self.uniqname+"@umich.edu"
        else:
            return self.alt_email


