from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.validators import validate_email, RegexValidator
from django.core.validators import MinValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from localflavor.us.models import PhoneNumberField
from stdimage import StdImageField

from mig_main.pdf_field import ContentTypeRestrictedFileField, pdf_types
from mig_main.location_field import LocationField


def resume_file_name(instance, filename):
    """ Returns the resume filename for a member.

    Fixes serialization loop issue.
    """
    return '/'.join([u"resumes", instance.uniqname+u'.pdf'])

PREFERENCES = [
        {
            'name': 'google_calendar_add',
            'values': ('always', 'never'),
            'verbose': ('Do you want to add events signed up for to your '
                        'personal calendar?'),
            'default': 'never',
        },
        {
            'name': 'google_calendar_account',
            'values': ('umich', 'alternate'),
            'verbose': 'Which email has your personal calendar',
            'default': 'umich',
        },
]

ALUM_MAIL_FREQ_CHOICES = (
    ("NO", "None"),
    ("YR", "Yearly"),
    ("SM", "Semesterly"),
    ("MO", "Monthly"),
    ("WK", "Weekly"),
    ("AC", "Remain Active Member"),
)

GENDER_CHOICES = (
    ("F", "Female"),
    ("M", "Male"),
    ("O", "Other/Prefer not to respond"),
)

PRONOUNS_CHOICES = (
    ("S", "She/Her"),
    ("H", "He/Him"),
    ("T", "They/Them"),
    ("Z", "Ze/Hir"),
    ("N", "No pronouns - Use my name"),
    ("A", "Ask me")
)

# homepage models
class SlideShowPhoto(models.Model):
    """ Photo that can be displayed on the home page.
    """
    photo = StdImageField(
                upload_to='home_page_photos',
                variations={'thumbnail': (1050, 790, True)}
    )
    active = models.BooleanField(default=False)
    title = models.TextField()
    text = models.TextField()
    link = models.CharField(max_length=256)


# general usage models
class AcademicTerm(models.Model):
    """ An individual term, e.g. Fall 2015.
    """
    year = models.PositiveSmallIntegerField(
                    validators=[MinValueValidator(1960)]
    )
    semester_type = models.ForeignKey('requirements.SemesterType')

    @classmethod
    def get_rchron_before(cls):
        """
        This gets all of the full terms prior to, and including, the current.

        While AcademicTerm objects do have a defined sort order, and thus
        sorted() could be used, this method is actually faster and allows for
        more ready exclusion of summer terms.
        """
        current = cls.get_current_term()
        query = Q(year__lte=current.year) & ~Q(semester_type__name='Summer')
        if current.semester_type.name == 'Winter':
            query = (query & ~
                     (Q(semester_type__name='Fall') &
                      Q(year=current.year)
                      )
                     )
        terms = cls.objects.filter(query)
        return terms.order_by('-year', '-semester_type')

    @classmethod
    def get_rchron(cls):
        return cls.objects.all().order_by('-year', '-semester_type')

    @classmethod
    def get_current_term(cls):
        current_terms = CurrentTerm.objects.all()
        if current_terms.exists():
            return current_terms[0].current_term
        return None

    def get_previous_full_term(self):
        new_type = self.semester_type.get_previous_full_type()
        if self.semester_type.name == 'Winter':
            new_year = self.year - 1
        else:
            new_year = self.year
        if self.__class__.objects.filter(
                            year=new_year,
                            semester_type=new_type).exists():
            return self.__class__.objects.get(
                        year=new_year,
                        semester_type=new_type)
        else:
            a = self.__class__(year=new_year, semester_type=new_type)
            a.save()
            return a

    def get_next_term(self):
        new_type = self.semester_type.get_next_type()
        if self.semester_type.name == 'Fall':
            new_year = self.year + 1
        else:
            new_year = self.year
        if self.__class__.objects.filter(
                            year=new_year,
                            semester_type=new_type).exists():
            return self.__class__.objects.get(
                        year=new_year,
                        semester_type=new_type)
        else:
            a = self.__class__(year=new_year, semester_type=new_type)
            a.save()
            return a

    def get_next_full_term(self):
        new_type = self.semester_type.get_next_full_type()
        if self.semester_type.name == 'Fall':
            new_year = self.year + 1
        else:
            new_year = self.year
        if self.__class__.objects.filter(
                            year=new_year,
                            semester_type=new_type).exists():
            return self.__class__.objects.get(
                        year=new_year,
                        semester_type=new_type)
        else:
            a = self.__class__(year=new_year, semester_type=new_type)
            a.save()
            return a

    def get_abbreviation(self):
        return self.semester_type.name[0]+str(self.year)

    def __unicode__(self):
        return self.semester_type.name + ' ' + unicode(self.year)

    def __gt__(self, term2):
        if not hasattr(term2, 'year'):
            return True
        if self.year > term2.year:
            return True
        if self.year < term2.year:
            return False
        return self.semester_type > term2.semester_type

    def __lt__(self, term2):
        if not hasattr(term2, 'year'):
            return False
        if self.year < term2.year:
            return True
        if self.year > term2.year:
            return False
        return self.semester_type < term2.semester_type

    def __eq__(self, term2):
        if not hasattr(term2, 'year'):
            return False
        if self.year != term2.year:
            return False
        return self.semester_type == term2.semester_type

    def __ne__(self, term2):
        return not self == term2

    def __le__(self, term2):
        return not self > term2

    def __ge__(self, term2):
        return not self < term2

    def __sub__(self, term2):
        if not hasattr(term2, 'year'):
            return 0
        years_diff = self.year-term2.year
        terms_diff = self.semester_type-term2.semester_type
        return 3*years_diff+terms_diff


class CurrentTerm(models.Model):
    """ The current term.

    There can only be one. This is slightly vestigial. An improvement was
    attempted and it didn't work, so we stuck with this.
    """
    current_term = models.ForeignKey(AcademicTerm)

    def __unicode__(self):
        return unicode(self.current_term)

    def save(self, *args, **kwargs):
        if CurrentTerm.objects.count() > 1:
            return
        if (CurrentTerm.objects.count() == 1 and
                not CurrentTerm.objects.get().id == self.id):
            return
        super(CurrentTerm, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if CurrentTerm.objects.count() <= 1:
            return
        super(CurrentTerm, self).delete(*args, **kwargs)


class TBPChapter(models.Model):
    """ A TBP Chapter.

    This will almost assuredly be incomplete, but it's unlikely to matter.
    """
    class Meta:
        verbose_name = 'TBP Chapter'
        verbose_name_plural = 'TBP Chapters'
    state = models.CharField(
                max_length=2,
                validators=[
                    RegexValidator(
                        regex=r'^[A-Z]{2}$',
                        message=('Must be the state (or territory) 2-letter'
                                 'code e.g. Michigan is MI')
                    )
                ]
    )
    letter = models.CharField(
                max_length=4,
                validators=[
                    RegexValidator(
                        regex=r'^[A-I,K-U,W-Z]+$',
                        message=('Greek letter (latin equivalent), e.g. Gamma'
                                 'is G, Theta is Q')
                    )
                ]
    )
    school = models.CharField(max_length=70)

    def __unicode__(self):
        return self.state+'-'+self.letter


class OfficerPosition(models.Model):
    """ One of the officer or chair positions within the chapter.
    """
    POSITION_TYPE_CHOICES = (
        ("O", "Officer"),
        ("C", "Chair"),
    )
    name = models.CharField(max_length=45)
    description = models.TextField()
    email = models.EmailField(max_length=254)
    enabled = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    position_type = models.CharField(
                        max_length=1,
                        choices=POSITION_TYPE_CHOICES,
                        default='O'
    )
    is_elected = models.BooleanField(default=True)
    TERM_LENGTH_CHOICES = (
        ('S', 'Semester'),
        ('A', 'Academic Year'),
        ('C', 'Calendar year'),
    )
    term_length = models.CharField(
                        max_length=1,
                        choices=TERM_LENGTH_CHOICES,
                        default='S',
    )

    @classmethod
    def get_current(cls):
        return cls.objects.filter(enabled=True).order_by('display_order')

    def __unicode__(self):
        return self.name

    def get_teams_led(self):
        return self.team_lead.exclude(
                    end_term__lte=AcademicTerm.get_current_term()
        )

    def get_teams(self):
        return self.members.exclude(
                    end_term__lte=AcademicTerm.get_current_term()
        )


class OfficerTeam(models.Model):
    """ An officer team is a grouping of officer positions around some
    functional area.

    This is generally not interacted with in terms of the website but is
    documented for informational purposes: officers are displayed by team on
    the leadership page.
    """
    name = models.CharField(max_length=80)
    lead = models.ForeignKey(OfficerPosition, related_name='team_lead')
    members = models.ManyToManyField(OfficerPosition, related_name='members')
    start_term = models.ForeignKey(
                    AcademicTerm,
                    related_name='teams_starting_in_term'
    )
    end_term = models.ForeignKey(
                    AcademicTerm,
                    related_name='teams_ending_in_term',
                    null=True,
                    blank=True
    )

    def __unicode__(self):
        return self.name


class Committee(models.Model):
    """ Used to display committee members, handle permissions.
    """
    name = models.CharField(max_length=128)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Standing(models.Model):
    """ Alumni, Grad, or Undergrad.
    """
    name = models.CharField(max_length=20)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Major(models.Model):
    """ Major area of study.
    """
    name = models.CharField(max_length=60)
    acronym = models.CharField(max_length=10)
    standing_type = models.ManyToManyField(Standing)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name+' ('+self.acronym+')'


class Status(models.Model):
    """ Active or Electee.
    """
    class Meta:
        verbose_name_plural = 'Statuses'
    name = models.CharField(max_length=20)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class ShirtSize(models.Model):
    """ Used for compiling member demographics, assisting with T-shirt orders.
    """
    name = models.CharField(max_length=35)
    acronym = models.CharField(max_length=4)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class UserPreference(models.Model):
    """ An individual preference key-value pair for a user.
    """
    user = models.ForeignKey('mig_main.UserProfile')
    preference_type = models.CharField(max_length=64)
    preference_value = models.CharField(max_length=64)

    def __unicode__(self):
        return unicode(self.user)+': '+self.preference_type


class UserProfile(models.Model):
    """ A generic user profile.

    Serves as the base class for other types of profiles (namely member).
    """
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    # Name Stuff
    nickname = models.CharField(max_length=40, blank=True)
    first_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=40)
    suffix = models.CharField(max_length=15, blank=True)
    maiden_name = models.CharField(max_length=40, blank=True, null=True)
    title = models.CharField(max_length=20, blank=True)
    uniqname = models.CharField(
                 max_length=8,
                 primary_key=True,
                 validators=[RegexValidator(
                               regex=r'^[a-z]{3,8}$',
                               message=('Your uniqname must be 3-8 characters,'
                                        'all lowercase.')
                            )
                            ]
    )

    # Methods
    @classmethod
    def get_users(cls):
        return cls.objects.all().order_by('last_name',
                                          'first_name',
                                          'uniqname'
                                          )

    def get_full_name(self):
        name = self.title+" " if self.title else ""
        name = name + self.first_name + " "
        name = name + self.middle_name+" " if self.middle_name else name
        name = name + '('+self.maiden_name+") " if self.maiden_name else name
        name = name + self.last_name
        name = name + ", "+self.suffix if self.suffix else name
        return name

    def __unicode__(self):
        return self.get_full_name()+" ("+self.uniqname+")"

    def __gt__(self, user2):
        if not hasattr(user2, 'last_name'):
            return True
        if self.last_name > user2.last_name:
            return True
        if self.last_name < user2.last_name:
            return False
        if not hasattr(user2, 'first_name'):
            return True
        if self.first_name > user2.first_name:
            return True
        if self.first_name < user2.first_name:
            return False
        if not hasattr(user2, 'middle_name'):
            return True
        return self.middle_name > user2.middle_name

    def __lt__(self, user2):
        if not hasattr(user2, 'last_name'):
            return False
        if self.last_name < user2.last_name:
            return True
        if self.last_name > user2.last_name:
            return False
        if not hasattr(user2, 'first_name'):
            return False
        if self.first_name < user2.first_name:
            return True
        if self.first_name > user2.first_name:
            return False
        if not hasattr(user2, 'middle_name'):
            return False
        return self.middle_name < user2.middle_name

    def __le__(self, user2):
        return not (self > user2)

    def __ge__(self, user2):
        return not (self < user2)

    def get_casual_name(self):
        if len(self.nickname) > 0:
            return self.nickname
        else:
            return self.first_name

    def get_firstlast_name(self):
        first_name = self.get_casual_name()
        if first_name == self.last_name:
            first_name = self.first_name
        middle = '('+self.maiden_name+") " if self.maiden_name else ''
        return first_name+' '+middle+self.last_name

    def get_email(self):
        return self.uniqname+"@umich.edu"

    def is_member(self):
        try:
            self.memberprofile
            return True
        except ObjectDoesNotExist:
            return False

    def is_electee(self):
        if not self.is_member():
            return False
        return self.memberprofile.status.name == 'Electee'

    def is_active(self):
        if not self.is_member():
            return False
        return self.memberprofile.status.name == 'Active'

    def is_ugrad(self):
        if not self.is_member():
            return False
        return self.memberprofile.standing.name == 'Undergraduate'

    def is_grad(self):
        if not self.is_member():
            return False
        return self.memberprofile.standing.name == 'Graduate'

    def is_alumni(self):
        if not self.is_member():
            return False
        return self.memberprofile.standing.name == 'Alumni'

class MemberProfile(UserProfile):
    """ A profile for a TBP member.

    The basic building block of almost everything on the site. Houses a
    member's information in terms of major, contact info, etc.
    """
    # Preferred Email address
    MAIL_PREF_CHOICES = (
        ("UM", "Umich email"),
        ("ALT", "Alternate email"),
    )

    # Classifications
    major = models.ManyToManyField(Major)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    UMID = models.CharField(
            max_length=8,
            validators=[RegexValidator(
                            regex=r'^[0-9]{8}$',
                            message="Your UMID must be 8 numbers."
                        )
                        ]
    )
    init_chapter = models.ForeignKey(
                    TBPChapter,
                    on_delete=models.PROTECT,
                    verbose_name="Initiating Chapter"
    )
    standing = models.ForeignKey(Standing, on_delete=models.PROTECT)
    alt_email = models.EmailField(
                    "Alternate email",
                    max_length=254,
                    blank=True
    )
    jobs_email = models.BooleanField(
                    "Receive corporate emails?",
                    default=True
    )
    alum_mail_freq = models.CharField(
                    "How frequently would you like alumni emails?",
                    max_length=2,
                    choices=ALUM_MAIL_FREQ_CHOICES,
                    default="WK"
    )
    preferred_email = models.CharField(
                            max_length=3,
                            choices=MAIL_PREF_CHOICES,
                            default="UM"
    )
    shirt_size = models.ForeignKey(ShirtSize, on_delete=models.PROTECT)
    short_bio = models.TextField()
    init_term = models.ForeignKey(
                        AcademicTerm,
                        on_delete=models.PROTECT,
                        verbose_name="Initiation term"
    )
    gender = models.CharField(
                        max_length=1,
                        choices=GENDER_CHOICES,
                        default="O"
    )
    pronouns = models.CharField(
                        max_length=1,
                        choices=PRONOUNS_CHOICES,
                        default="A"
    )
    expect_grad_date = models.DateField("Expected graduation date")
    still_electing = models.BooleanField(default=True)
    photo = StdImageField(
                upload_to='member_photos',
                variations={'thumbnail': (555, 775)}
    )
    resume = ContentTypeRestrictedFileField(
        upload_to=resume_file_name,
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=True
    )
    phone = PhoneNumberField()
    location = LocationField(blank=True)

    # Methods
    @classmethod
    def get_members(cls, include_alums=True):
        query = Q(status__name='Active') | Q(status__name='Electee',
                                             still_electing=True)
        if include_alums:
            output = cls.objects.filter(query)
        else:
            output = cls.objects.filter(query).exclude(standing__name='Alumni')

        return output.order_by('last_name',
                               'first_name',
                               'uniqname')
            

    @classmethod
    def get_actives(cls):
        query = Q(status__name='Active')
        return cls.objects.filter(query).order_by('last_name',
                                                  'first_name',
                                                  'uniqname')

    @classmethod
    def get_electees(cls):
        query = Q(status__name='Electee', still_electing=True)
        return cls.objects.filter(query).order_by('last_name',
                                                  'first_name',
                                                  'uniqname')

    def get_num_terms_distinction(self, distinction):
        distinctions = self.distinction_set.filter(
                            distinction_type=distinction
        )
        return distinctions.count()

    def get_email(self):
        if self.preferred_email == "UM" or not self.alt_email:
            return self.uniqname+"@umich.edu"
        else:
            return self.alt_email

    def save(self, *args, **kwargs):
        super(MemberProfile, self).save(*args, **kwargs)
        cache.delete('active_list_html')

    def delete(self, *args, **kwargs):
        super(MemberProfile, self).delete(*args, **kwargs)
        cache.delete('active_list_html')

    def get_resume_name(self):
        if not self.resume:
            return None
        return slugify(self.last_name +
                       '_' + self.first_name + '_' + self.uniqname) + '.pdf'


class TBPraise(models.Model):
    """ An object used to send (potentially anonymous) praise to another
    member for something good that they've done.
    """
    giver = models.ForeignKey(UserProfile, related_name='praise_giver')
    recipient = models.ForeignKey(UserProfile, related_name='praise_recipient')
    description = models.TextField()
    public = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    date_added = models.DateField(auto_now_add=True)

    PRAISE_BODY = r'''Hello %(name)s
This is an automated notice that %(sender)s has sent you a personal
affirmation, TBPraise if you will. The details are below:

%(praise)s

%(public_bit)s

If you have any questions, please let the Website Chair know
(tbp-website@umich.edu).

Regards,
The Website

If you'd like, you can pay it forward by sending an affirmation to another
member:
https://tbp.engin.umich.edu%(link)s'''

    def is_public(self):
        return self.approved and self.public

    def email_praise(self):
        persons_name = self.recipient.get_casual_name()
        if self.anonymous:
            sender = 'someone'
            subject = '[TBP] You\'ve been sent an affirmation'
        else:
            sender = self.giver.get_firstlast_name()
            subject = '[TBP] %s has sent you an affirmation' % (sender)
        if self.public:
            rel_link = reverse('member_resources:approve_praise',
                               args=(self.id,))
            link = 'https://tbp.engin.umich.edu%(link)s' % {'link': rel_link}
            public_bit = ('Pending your approval, this message will appear on '
                          'the website so that other\'s know about your '
                          'awesomeness. To approve the affirmation for posting'
                          ' click here: ')+link
        else:
            public_bit = ''
            public_take_down = ''
        body = self.PRAISE_BODY % {
                    'name': persons_name,
                    'public_bit': public_bit,
                    'sender': sender,
                    'praise': self.description,
                    'link': reverse('member_resources:submit_praise')
        }
        send_mail(
                subject,
                body,
                'tbp.mi.g@gmail.com',
                [self.recipient.get_email()],
                fail_silently=True
        )
