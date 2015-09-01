import itertools

from django.core.mail import send_mass_mail
from django.db import models

from localflavor.us.models import PhoneNumberField

from mig_main.pdf_field import ContentTypeRestrictedFileField, pdf_types
from mig_main.models import OfficerPosition
# Create your models here.


class Company(models.Model):
    """ Represents an actual company.

    A Company is generally a building block defined more by how other models
    interact with it than by anything intrinsic to its own construction.
    """
    name = models.CharField(max_length=256)
    hq_location = models.CharField('HQ Location',max_length=256)
    job_field = models.ManyToManyField('corporate.JobField')

    def __unicode__(self):
        return self.name


class CompanyContact(models.Model):
    """ Represent the contacts for the chapter's corporate relations program.

    An abstract base class that defines much of the interface for interacting
    with contacts.
    """
    class Meta:
        abstract = True

    address = models.CharField(max_length=256, blank=True)
    company = models.ForeignKey(Company)
    gets_email = models.BooleanField(default=False)
    has_contacted = models.BooleanField(default=False)
    personal_contact_of = models.ForeignKey(
            'mig_main.MemberProfile',
            related_name='%(class)s_personal_contacts',
            null=True,
            blank=True
    )
    speaking_interest = models.BooleanField(default=False)

    @classmethod
    def get_contacts(cls, **kwargs):
        """ Returns a list of all the contacts associated with the provided
        query.
        """
        return itertools.chain(
                *[u.objects.filter(**kwargs) for u in cls.__subclasses__()]
        )

    def get_email(self):
        """ Returns the email for the contact """
        pass

    def get_phone(self):
        """ Returns the phone number for the contact """
        pass

    def get_name(self):
        """ Returns the name (first last) for the contact """
        pass

    def get_bio(self):
        """ Returns the bio for the contact or None if empty """
        pass

    def is_member(self):
        """Returns True if the contact is a MI-G member."""
        pass

    def is_member_other_chapter(self):
        """Returns True if the contact is a TBP but not a MI-G member."""
        pass


class CorporateEmail(models.Model):
    """ Represents an email to be sent to the corporate contacts list.

    Provides an interface for creating and sending such emails.
    """
    active = models.BooleanField(default=True)
    mig_alum_text = models.TextField()
    other_tbp_alum_text = models.TextField()
    previous_contact_text = models.TextField()
    salutation = models.CharField(max_length=64)
    subject = models.CharField(max_length=512)
    text = models.TextField()

    def send_corporate_email(self):
        """ Sends the email to all company contacts who should receive it."""
        contacts = CompanyContact.get_contacts(gets_email=True)
        email_tuple = (self.email_contact(contact) for contact in contacts)
        send_mass_mail(email_tuple)

    def preview_email(
            self,
            mig_alum=False,
            other_alum=False,
            previous_contact=False,
            personal_contact=False):
        """ Returns an example email based on the flags provided.

        Used to spot check emails before sending.
        """

        if mig_alum:
            replace_text = self.mig_alum_text
        elif other_alum:
            replace_text = self.other_tbp_alum_text
        elif previous_contact:
            replace_text = self.previous_contact_text
        elif personal_contact:
            replace_text = ('CONTACT_NAME said that you may be interested in'
                            'being involved with our chapter.')
        else:
            replace_text = ''
        text = self.text.replace('<<extra_text>>', replace_text)
        body = r''' %(salutation)s Company Representative:

%(text)s
''' % {'salutation': self.salutation, 'text': text}
        subject = self.subject.replace('<<company_name>>', 'COMPANY')
        return 'SUBJECT: ' + subject + '\n\n' + 'BODY: ' + body

    def email_contact(self, company_contact):
        """ Creates an email to the provided contact. """
        cr = OfficerPosition.objects.filter(name='Corporate Relations Officer')
        if not cr.exists():
            return None
        cro_email = cr[0].email
        if company_contact.is_member():
            replace_text = self.mig_alum_text
        elif company_contact.is_member_other_chapter():
            replace_text = self.other_tbp_alum_text
        elif company_contact.has_contacted:
            replace_text = self.previous_contact_text
        elif company_contact.personal_contact_of:
            contact = company_contact.personal_contact_of.get_firstlast_name()
            replace_text = contact + ('said that you may be interested in'
                                      'being involved with our chapter.')
        else:
            replace_text = ''
        text = self.text.replace('<<extra_text>>', replace_text)
        body = ('%(salutation)s %(name)s:\n\n'
                '%(text)s')
        body = body % {'salutation': self.salutation,
                       'text': text,
                       'name': company_contact.get_name()}
        subject = self.subject.replace('<<company_name>>',
                                       company_contact.company.name)
        return (subject, body, cro_email, [company_contact.get_email()])


class CorporateResourceGuide(models.Model):
    """ A Django model for keeping track of the corporate resource guide pdf

    Instances of this class keep track of the currently used, and all previous
    versions, of the corporate resource guide. The active version of this guide
    is used in mass emails, in resume zip files, and in other corporate
    activities.
    """
    active = models.BooleanField(default=False)
    name = models.CharField(max_length=64)
    resource_guide = ContentTypeRestrictedFileField(
        upload_to='corporate_resources',
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=False
    )

    def __unicode__(self):
        return self.name + (' (active)' if self.active else '')


class CorporateTextField(models.Model):
    """ Allows customization of the corporate resources landing page.

    The Corporate landing page is broken up into sections where the text may be
    provided by the Corporate Relations Officer. These sections are provided in
    instances of this class. Only one instance of this model may exist for a
    particular section.

    The section "Other" is not used at this time and is reserved for future
    expansion.
    """
    CHOICES = (
            ('OP', 'Corporate Involvement Opportunities'),
            ('CT', 'Contact'),
            ('OT', 'Other'),
    )
    section = models.CharField(
                max_length=2,
                choices=CHOICES,
                default='OP',
                unique=True
    )
    text = models.TextField()

    def __unicode__(self):
        return 'Corporate Text for '+self.get_section_display()


class EmploymentExperienceBase(models.Model):
    """ Abstract Base Class consolidating the common attributes for different
    experience types.
    """
    class Meta:
        abstract = True

    DEGREES = [
        ('N', 'None'),
        ('B', 'Bachelors'),
        ('M', 'Masters'),
        ('D', 'Doctorate'),
    ]
    REGIONS = [
        ('MW', 'Midwest'),
        ('NE', 'Northeast'),
        ('NW', 'Northwest'),
        ('SE', 'Southeast'),
        ('SW', 'Southwest'),
        ('IN', 'International'),
    ]
    commentary = models.TextField()
    company = models.ForeignKey(Company)
    highest_degree = models.CharField(max_length=1, choices=DEGREES)
    job_type = models.ForeignKey('corporate.JobType')
    major = models.ManyToManyField('mig_main.Major')
    region = models.CharField(max_length=2, choices=REGIONS)


class Interview(models.Model):
    """ An interview review provided for the internal 'glass door'.

    Contains information on the format of the interview and also on how it
    went.
    """
    CONNECTIONS = [
        ('STCF', 'SWE/TBP Career Fair'),
        ('OCF', 'Other Career Fair'),
        ('WEB', 'Online Only'),
        ('P', 'Personal Contact'),
        ('INT', 'Internship/Co-op Conversion'),
    ]
    DIFFICULTIES = [
        ('1', '1: Easy'),
        ('2', '2'),
        ('3', '3: Average'),
        ('4', '4'),
        ('5', '5: Hard'),
    ]
    EXPERIENCES = [
        ('+', 'Positive'),
        ('N', 'Neutral'),
        ('-', 'Negative'),
    ]
    INTERVIEW_FORMS = [
        ('F', 'Phone'),
        ('1', 'One-on-one'),
        ('P', 'Panel'),
        ('G', 'Group'),
    ]
    INTERVIEW_LOCATIONS = [
        ('P', 'Phone'),
        ('S', 'On-site'),
        ('C', 'On-campus'),
        ('O', 'Other'),
    ]
    INTERVIEW_TYPES = [
        ('B', 'Behavioral'),
        ('T', 'Technical'),
        ('+', 'Both'),
        ('O', 'Other'),
    ]
    OUTCOMES = [
        ('N', 'Not Offered'),
        ('D', 'Declined Offer'),
        ('A', 'Accepted Offer'),
    ]

    comments = models.TextField()
    company = models.ForeignKey(Company)
    difficulty = models.CharField(max_length=1, choices=DIFFICULTIES)
    experience = models.CharField(max_length=1, choices=EXPERIENCES)
    how_connected = models.CharField(max_length=4, choices=CONNECTIONS)
    interview_form = models.CharField(max_length=1, choices=INTERVIEW_FORMS)
    interview_type = models.CharField(max_length=1, choices=INTERVIEW_TYPES)
    job_title = models.CharField(max_length=256)
    job_type = models.ForeignKey('corporate.JobType')
    location = models.CharField(max_length=1, choices=INTERVIEW_LOCATIONS)
    outcome = models.CharField(
                max_length=1,
                choices=OUTCOMES,
                blank=True,
                null=True,
    )

    @classmethod
    def get_company_interview_experience(cls, company, job_type=None):
        """ Returns a 3-tuple with the number of experience ratings
        (Positive, Neutral, Negative) for a particular company.

        If job_type is specified, only the Interview objects for that JobType
        are considered. If the query is empty or the number of ratings is less
        than 3, it returns None.
        """
        pass
        # TODO: Implementation

    @classmethod
    def get_company_interview_difficulty(cls, company, job_type=None):
        """ Returns the average difficulty of interviews for a particular
        company.

        If job_type is specified, only the Interview objects for that JobType
        are considered. If the query is empty or the number of ratings is less
        than 3, it returns None.
        """
        pass
        # TODO: Implementation

    @classmethod
    def get_company_interview_outcomes(cls, company, job_type=None):
        """ Returns a 3-tuple with the number of outcomes
        (Not offered, Declined offer, Accepted Offer) for a particular company.

        If job_type is specified, only the Interview objects for that JobType
        are considered. If the query is empty or the number of ratings is less
        than 3, it returns None.
        """
        pass
        # TODO: Implementation

    @classmethod
    def get_company_interviews(cls, company, job_type=None):
        """ Returns a queryset of Interview objects for a particular company.

        If job_type is specified, only the Interview objects for that JobType
        are considered. If the query is empty or the number of ratings is less
        than 3, it returns None.
        """
        pass
        # TODO: Implementation


class InterviewQuestion(models.Model):

    INTERVIEW_TYPES = [
        ('B', 'Behavioral'),
        ('T', 'Technical'),
        ('O', 'Both/Other'),
    ]
    company = models.ForeignKey(Company)
    job_type = models.ForeignKey('corporate.JobType')
    question = models.TextField()
    question_type = models.CharField(max_length=1, choices=INTERVIEW_TYPES)

    @classmethod
    def get_questions(cls, **kwargs):
        """ Returns a queryset of InterviewQuestions for the provided query.
        """
        return cls.objects.filter(**kwargs)


class JobExperience(EmploymentExperienceBase):
    """ Subclass of EmploymentExperienceBase"""
    EXPERIENCES = [
        ('+', 'Positive'),
        ('N', 'Neutral'),
        ('-', 'Negative'),
    ]
    years = models.PositiveSmallIntegerField(
                        verbose_name=('If internship, years in school. If '
                                      'fulltime, years with the company')
    )
    overall_rating = models.CharField(
                        max_length=1,
                        choices=EXPERIENCES
    )

    @classmethod
    def get_company_rating(company, **kwargs):
        """ Returns a 3-tuple with company ratings.

        Returns a 3-tuple with the number of ratings (Positive, Neutral,
        Negative) for a particular company and the provided filtering options
        in kwargs. If the query is empty or the number of reviews is less than
        3, it returns None.
        """
        pass
        # TODO: Implementation

    @classmethod
    def get_company_comments(company, **kwargs):
        """ Returns a value queryset of JobExperience objects for the company.

        Returns a value queryset of the JobExperience objects submitted for a
        particular company and the provided filtering options. If the query is
        empty or the number of reviews is less than 3, it returns None.

        Additionally, for each object returned, it attempts to include as much
        information as possible. It adds attributes until the combination of
        attributes, if searched would result in too small a sample (fewer than
        3 results). It adds attributes in the order: job_type, major,
        highest_degree, years, region.
        """
        pass
        # TODO: Implementation


class JobField(models.Model):
    """ These represent the different industries a company may be part of. This
    is mostly defined by how other models interact with it.
    """

    name = models.CharField(max_length=256, verbose_name='Industry Name')
    majors = models.ManyToManyField(
                        'mig_main.Major',
                        verbose_name='Majors hired in the industry'
    )
    def __unicode__(self):
        return self.name

class JobType(models.Model):
    """ The type of job (internship, LDP, etc.)

    These will be created outside of the website work flow and will be
    predefined to include internships, co-ops, leadership development
    programs/rotational programs (e.g. Edison, WERLD, FCG), contract/agency,
    direct hire (default full-time).
    """

    name = models.CharField(max_length=256, verbose_name='Name of job Type')
    is_full_time = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name


class MemberContact(CompanyContact):
    """ Subclass of CompanyContact. Overrides the instance methods to work with
    MemberProfiles.
    """

    member = models.ForeignKey('mig_main.MemberProfile')

    def get_email(self):
        """ Returns the email for the contact """
        return self.member.get_email()

    def get_phone(self):
        """ Returns the phone number for the contact """
        return self.member.phone

    def get_name(self):
        """ Returns the name (first last) for the contact """
        return self.member.get_firstlast_name()

    def get_bio(self):
        """ Returns the bio for the contact or None if empty """
        return self.member.short_bio

    def is_member(self):
        """Returns True if the contact is a MI-G member."""
        return True

    def is_member_other_chapter(self):
        """Returns True if the contact is a TBP but not a MI-G member."""
        return False


class NonMemberContact(CompanyContact):
    """ Subclass of CompanyContact. Overrides the instance methods to work
    without MemberProfiles.
    """

    name = models.CharField(max_length=256, verbose_name='Full name')
    email = models.EmailField(max_length=254, blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    short_bio = models.TextField(blank=True, null=True)
    initiating_chapter = models.ForeignKey('mig_main.TBPChapter',
                                           blank=True,
                                           null=True)

    def get_email(self):
        """ Returns the email for the contact """
        return self.email

    def get_phone(self):
        """ Returns the phone number for the contact """
        return self.phone

    def get_name(self):
        """ Returns the name (first last) for the contact """
        return self.name

    def get_bio(self):
        """ Returns the bio for the contact or None if empty """
        return self.short_bio

    def is_member(self):
        """Returns True if the contact is a MI-G member."""
        if self.initiating_chapter:
            return (self.initiating_chapter.state == 'MI' and
                    self.initiating_chapter.letter == 'G')
        return False

    def is_member_other_chapter(self):
        """Returns True if the contact is a TBP but not a MI-G member."""
        if self.is_member():
            return False
        if self.initiating_chapter:
            return True
        return False


class OfferDetails(EmploymentExperienceBase):
    """ Subclass of EmploymentExperienceBase"""

    salary = models.PositiveSmallIntegerField('Starting Monthly Salary (USD)')
    number_of_vacation_days = models.PositiveSmallIntegerField()
    signing_bonus = models.PositiveSmallIntegerField('Signing Bonus (USD)')

    @classmethod
    def get_salary_data(cls, **kwargs):
        """ Get a dictionary of salary data for the provided query

        Returns a dictionary with statistical data on salary, vacation days,
        and signing bonus for the given query (Company, major, etc.). If the
        query is empty or the number of reviews is less than 3, it returns
        None. The dictionary entries are avg_salary,
        avg_number_of_vacation_days, min_signing_bonus, max_salary, etc.
        """
        pass
        # TODO: Implementation
