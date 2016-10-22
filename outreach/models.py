from datetime import date

from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from stdimage import StdImageField

from mig_main.pdf_field import ContentTypeRestrictedFileField, pdf_types

presentation_types = pdf_types + [
    'application/vnd.ms-powerpoint',
    ('application/vnd.openxmlformats-'
     'officedocument.presentationml.presentation'),
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
    'application/vnd.ms-powerpoint.presentation.macroEnabled.12',
    'application/vnd.ms-powerpoint.slideshow.macroEnabled.12'
]

worksheet_types = pdf_types + [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-word.document.macroEnabled.12'
]


# Create your models here.
class OutreachPhotoType(models.Model):
    """ Category of outreach photo. Used for determining where to display
    the photo.
    """
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class OutreachPhoto(models.Model):
    """ A photo to display on the outreach section. """
    photo = StdImageField(
                upload_to='outreach_photos',
                variations={'thumbnail': (1050, 790)}
    )
    photo_type = models.ForeignKey(OutreachPhotoType)
    active = models.BooleanField(default=False)
    title = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=256, blank=True)

    def __unicode__(self):
        return self.title + 'Photo'


class MindSETModule(models.Model):
    """ One of the MindSET Modules, repository for information.
    """
    title = models.CharField(max_length=128)
    concepts = models.TextField()
    presentation = ContentTypeRestrictedFileField(
        upload_to='mindset_module_presentations',
        content_types=presentation_types,
        max_upload_size=262144000,
        blank=True
    )
    worksheet = ContentTypeRestrictedFileField(
        upload_to='mindset_module_worksheets',
        content_types=worksheet_types,
        max_upload_size=262144000,
        blank=True
    )

    def __unicode__(self):
        return self.title


class MindSETProfileAdditions(models.Model):
    """ Extra info to display on the website for mindset officers.
    """
    mindset_bio = models.TextField()
    favorite_ice_cream = models.CharField(max_length=128)
    favorite_city = models.CharField(max_length=128)
    fun_fact = models.TextField()
    user = models.OneToOneField('mig_main.MemberProfile')


class VolunteerFile(models.Model):
    """ Files needed by volunteers e.g. the background check form.
    """
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    the_file = ContentTypeRestrictedFileField(
        upload_to='mindset_volunteer_files',
        content_types=pdf_types,
        max_upload_size=262144000,
        blank=False
    )


class TutoringRecord(models.Model):
    """ A record of someone tutoring. Used to track tutoring participation
    and hours.
    """
    date_tutored = models.DateField(default=date.today)
    tutor = models.ForeignKey('mig_main.MemberProfile')
    student_uniqname = models.CharField(
                        'Tutored student\'s uniqname',
                        max_length=8,
                        validators=[
                            RegexValidator(
                                regex=r'^[a-z]{3,8}$',
                                message=('The tutored student\'s uniqname '
                                         'must be 3-8 characters, all '
                                         'lowercase.'),
                            )
                        ]
    )
    number_hours = models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        validators=[MinValueValidator(0)]
    )
    courses_tutored = models.TextField()
    topics_covered_and_comments = models.TextField(blank=True)
    approved = models.BooleanField(default=False)


class TutoringPageSection(models.Model):
    """ One of the subpages of the tutoring page.
    """
    page_title = models.CharField(max_length=128)
    page_content = models.TextField()
    page_order = models.PositiveSmallIntegerField()
    members_only = models.BooleanField(default=False)


class OutreachEventType(models.Model):
    """ A type of outreach event that will display on the website.

    Each gets its own page.
    """
    event_category = models.OneToOneField(
                        'requirements.EventCategory')
    title = models.CharField(max_length=256)
    text = models.TextField()
    url_stem = models.CharField(
                    max_length=64,
                    unique=True,
                    validators=[
                        RegexValidator(
                            regex=r'^[a-z,_]+$',
                            message='The url stem must use only the lowercase '
                                    'letters a-z and the underscore.'
                        )
                    ]
    )
    officers_can_edit = models.ManyToManyField('mig_main.OfficerPosition')
    tab_name = models.CharField(max_length=64, blank=True, null=True)
    has_calendar_events = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(visible=True)

    def __unicode__(self):
        return self.title

    def get_tab_name(self):
        if self.tab_name:
            return self.tab_name
        return self.event_category.name


class OutreachEvent(models.Model):
    """ An individual outreach event to display.

    These include inforamtion about signing up for non-members.
    """
    outreach_event = models.ForeignKey(OutreachEventType)
    banner = StdImageField(upload_to='outreach_event_banners')
    google_form_link = models.CharField(max_length=256, blank=True, null=True)
    pin_to_top = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Event # '+unicode(self.id)+' for '+unicode(self.outreach_event)
