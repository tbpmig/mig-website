from django.db import models
from stdimage import StdImageField

# Create your models here.
class AboutSlideShowPhoto(models.Model):
    photo   = StdImageField(upload_to='about_page_photos',thumbnail_size=(1050,790))
    active  = models.BooleanField()
    title   = models.TextField()
    text    = models.TextField()
    link    = models.CharField(max_length=256,blank=True)

class JoiningTextField(models.Model):
    CHOICES = (
            ('EL','Eligibility Requirements'),
            ('Y','Why Join TBP'),
            ('UG','Requirements to Join (Undergrads)'),
            ('GR','Requirements to Join (Grads)'),
    )
    section = models.CharField(max_length=2,choices=CHOICES,default='EL')
    text = models.TextField()

