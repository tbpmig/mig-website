"""
The models file for the about app/module.
"""
from django.db import models
from stdimage import StdImageField


# Create your models here.
class AboutSlideShowPhoto(models.Model):
    """
    Necessary information for the images used for
    the slideshow on the about page.
    """
    photo = StdImageField(upload_to='about_page_photos',
                          variations={'thumbnail': (1050, 790)})
    active = models.BooleanField(default=False)
    title = models.TextField()
    text = models.TextField()
    link = models.CharField(max_length=256, blank=True)

    def __unicode__(self):
        active_string = ' (inactive)' if not self.active else ''
        return 'Photo: \"' + self.title + '\"' + active_string


class JoiningTextField(models.Model):
    """
    Text for one of the sections of the joining page:
    :view:`about.views.eligibility`.
    
    Allows a user to select a section and add text for it so that
    editing of html is not required.
    
    ``CHOICES`` attribute:

    EL
        Eligibility Requirements

    Y   
        Why Join TYP

    UG
        Requirements to Join for Undergrads

    GR
        Requirements to Join for Grads

    """
    CHOICES = (
            ('EL', 'Eligibility Requirements'),
            ('Y', 'Why Join TBP'),
            ('UG', 'Requirements to Join (Undergrads)'),
            ('GR', 'Requirements to Join (Grads)'),
    )
    section = models.CharField(
                max_length=2,
                choices=CHOICES,
                default='EL',
                help_text=('One of the sections defined by the CHOICES '
                           'attribute:')                           
    )
    text = models.TextField(
            help_text=('The text which should be displayed for the section. '
                       'Supports markdown formatting.')
    )

    def __unicode__(self):
        return 'Joining Text for: '+self.get_section_display()
