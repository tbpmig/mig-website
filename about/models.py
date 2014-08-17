"""
The models file for the about app/module.
"""

from django.db import models
from stdimage import StdImageField

# Create your models here.
class AboutSlideShowPhoto(models.Model):
    """
    Necessary information for the images used for the slideshow on the about page. 
    """
    photo   = StdImageField(upload_to='about_page_photos',variations={'thumbnail':(1050,790)})
    active  = models.BooleanField()
    title   = models.TextField()
    text    = models.TextField()
    link    = models.CharField(max_length=256,blank=True)

class JoiningTextField(models.Model):
    """
    Text for one of the sections of the joining page. Can select a section and add text for it so that editing of html is not required.
    """
    CHOICES = (
            ('EL','Eligibility Requirements'),
            ('Y','Why Join TBP'),
            ('UG','Requirements to Join (Undergrads)'),
            ('GR','Requirements to Join (Grads)'),
    )
    section = models.CharField(max_length=2,choices=CHOICES,default='EL')
    text = models.TextField()

