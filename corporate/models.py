from django.db import models

from mig_main.pdf_field import ContentTypeRestrictedFileField,pdf_types

# Create your models here.
class CorporateTextField(models.Model):
    CHOICES = (
            ('OP','Corporate Involvement Opportunities'),
            ('CT','Contact'),
            ('OT','Other'),
    )
    section = models.CharField(max_length=2,choices=CHOICES,default='OP')
    text = models.TextField()
    def __unicode__(self):
        return 'Corporate Text for '+self.get_section_display()

class CorporateResourceGuide(models.Model):
    active          =models.BooleanField(default=False)
    name            =models.CharField(max_length=64)
    resource_guide          = ContentTypeRestrictedFileField(
        upload_to='corporate_resources',
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=False
    )
    def __unicode__(self):
        return self.name + ' (active)' if self.active else ''
