from django.db import models
from localflavor.us.models import PhoneNumberField
from stdimage import StdImageField

from mig_main.pdf_field import ContentTypeRestrictedFileField,pdf_types



# Create your models here.
class Officer(models.Model):
    user            = models.ForeignKey('mig_main.MemberProfile',
                                        on_delete=models.PROTECT)   
    term            = models.ManyToManyField('mig_main.AcademicTerm')
    position        = models.ForeignKey('mig_main.OfficerPosition',
                                        on_delete=models.PROTECT)
    website_bio     = models.TextField()
    website_photo   = StdImageField(upload_to='officer_photos',thumbnail_size=(555,775))
    def __unicode__(self):
        return self.user.get_full_name()+': '+self.position.name

class Distinction(models.Model):
    member          = models.ForeignKey('mig_main.MemberProfile')
    term            = models.ForeignKey('mig_main.AcademicTerm')
    distinction_type= models.ForeignKey('requirements.DistinctionType')
    gift            = models.CharField(max_length=128)
    def __unicode__(self):
        return unicode(self.term)+' '+unicode(self.distinction_type)+' for '+unicode(self.member)
        
class WebsiteArticle(models.Model):
    created_by      = models.ForeignKey('mig_main.MemberProfile',
                                        on_delete = models.SET_NULL,
                                        null=True,related_name='article_created_by')
    title           = models.CharField(max_length=250)
    body            = models.TextField()
    date_posted     = models.DateField()
    tagged_members  = models.ManyToManyField('mig_main.MemberProfile', blank=True,
                                            null=True,default=None,related_name='article_tagged_members')
    def __unicode__(self):
        return self.title+' ('+str(self.date_posted)+')'
class Publication(models.Model):
    date_published  = models.DateField()
    volume_number   = models.PositiveSmallIntegerField()
    edition_number  = models.PositiveSmallIntegerField()
    name            = models.CharField(max_length=70)
    PUBlICATION_TYPES=[
                    ('CS','Cornerstone'),
                    ('AN','Alumni News')
                ]
    type            = models.CharField(max_length=2,
                                        choices=PUBlICATION_TYPES,
                                        default='CS')
    pdf_file        = ContentTypeRestrictedFileField(
        upload_to='newsletters',
        content_types=pdf_types,
        max_upload_size=104857600,
    )
    def __unicode__(self):
        return self.name
class MeetingMinutes(models.Model):
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='minutes',
            content_types=pdf_types,
            max_upload_size=104857600,
    )
    MEETING_TYPES=[
            ('NI','New Initiatives'),
            ('MM','Main Meetings'),
            ('OF','Officer Meetings'),
            ('AD','Advisory Board Meetings'),
        ]
    meeting_type = models.CharField(max_length=2,
            choices=MEETING_TYPES,
            default='MM')
    semester = models.ForeignKey('mig_main.AcademicTerm')
    meeting_name = models.CharField(max_length=80)
    def __unicode__(self):
        return self.meeting_name+' minutes.'

class GoverningDocumentType(models.Model):
    name = models.CharField(max_length=40)
    def __unicode__(self):
        return self.name

class GoverningDocument(models.Model):
    document_type = models.ForeignKey(GoverningDocumentType)
    active = models.BooleanField(default=True)
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='governing_docs',
            content_types=pdf_types,
            max_upload_size=104857600,
    )
    def __unicode__(self):
        if self.active:
            return 'Current '+unicode(self.document_type)
        else:
            return 'Old '+unicode(self.document_type)
class AwardType(models.Model):
    name = models.CharField(max_length=256)
    def __unicode__(self):
        return self.name

class Award(models.Model):
    award_type = models.ForeignKey(AwardType)
    term = models.ForeignKey('mig_main.AcademicTerm')
    recipient = models.ForeignKey('mig_main.MemberProfile')
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return unicode(self.award_type)+' for '+unicode(self.term)+': '+unicode(self.recipient)
class ProjectReport(models.Model):
    name = models.CharField(max_length=128, verbose_name='Project Name')
    term        = models.ForeignKey('mig_main.AcademicTerm')
    relation_to_TBP_objectives=models.TextField()
    
    is_new_event    = models.BooleanField(default=False)
    
    organizing_hours= models.PositiveSmallIntegerField()
    planning_start_date = models.DateField()
    TARGET_AUDIENCE_CHOICES = [
                        ('COMM','Community'),
                        ('UNIV','University'),
                        ('PROF','Profession'),
                        ('CHAP','Chapter'),
                        ('HON','Honors/Awards')
                    ]
    target_audience         = models.CharField(max_length=4,
                                                choices=TARGET_AUDIENCE_CHOICES,
                                                default='COMM')
    

    #Contact info: 
    contact_name            = models.CharField(max_length=75,
                                                blank=True)
    contact_email           = models.EmailField(max_length=254,
                                                blank=True)
    contact_phone_number    = PhoneNumberField(blank=True)
    contact_title           = models.CharField(max_length=75,
                                                blank=True)
    other_info              = models.CharField(max_length=150,
                                                blank=True)
    other_group             = models.CharField(max_length=60,
                                                blank=True)
    
    general_comments        = models.TextField()
    
    items                   = models.TextField()
    
    cost                    = models.PositiveIntegerField()
    
    problems_encountered    = models.TextField()
    
    recommendations         = models.TextField()
    evaluations_and_results = models.TextField()
    
    one_to_five =[('1','1:Best'),('2','2'),('3','3'),('4','4'),('5','5: Worst')]
    rating                  = models.CharField(max_length=1,
                                                choices=one_to_five,
                                                default='3')
    best_part               = models.TextField()
    opportunity_to_improve  = models.TextField()
    recommend_continuing    = models.BooleanField()

    def __unicode__(self):
        return self.name
