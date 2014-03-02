from datetime import date, timedelta

from django.db import models
from django.core.validators import MaxValueValidator, RegexValidator


class Election(models.Model):
    term        = models.ForeignKey('mig_main.AcademicTerm')
    open_date = models.DateField(default=date.today())
    close_date= models.DateField(default=date.today()+timedelta(weeks=3))
    
    def __unicode__(self):
        return str(self.term)+" Election"
        
class TempNomination(models.Model):
    name        = models.CharField(max_length=50,verbose_name='Nominee\'s name')
    election    = models.ForeignKey(Election)
    nominee     = models.CharField(max_length=8,verbose_name='Nominee\'s uniqname')
    position    = models.ForeignKey('mig_main.OfficerPosition')
    accepted    = models.NullBooleanField(default=None)

class Nomination(models.Model): 
    election    = models.ForeignKey(Election)
    nominee     = models.ForeignKey('mig_main.MemberProfile', related_name='nominee')
    nominator   = models.ForeignKey('mig_main.UserProfile', related_name='nominator',
                                    null=True, blank=True, on_delete=models.SET_NULL)
    position    = models.ForeignKey('mig_main.OfficerPosition')
    accepted    = models.NullBooleanField(default=None)

    
    def __unicode__(self):
        return self.nominee.get_full_name()+" nominated for "+self.position.name
