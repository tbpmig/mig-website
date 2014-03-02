from django.db import models
from django.core.validators import  RegexValidator,MinValueValidator

# Create your models here.


class DistinctionType(models.Model):
    #Electee, Active, DA, PA
    name = models.CharField(max_length = 30)
    status_type = models.ForeignKey('mig_main.Status')
    standing_type = models.ManyToManyField('mig_main.Standing')
    def __unicode__(self):
        return self.name
class SemesterType(models.Model):
    #Summer, Fall, Winter
    name = models.CharField(max_length = 30)
    def __unicode__(self):
        return self.name+' semester'
        
class EventCategory(models.Model):
    parent_category = models.ForeignKey('self',null=True,blank=True,default=None)
    name            = models.CharField(max_length=30)
    def __unicode__(self):
        return self.name

class MembershipAchievement(models.Model):
    distinction = models.ForeignKey(DistinctionType)
    term        = models.ForeignKey('mig_main.AcademicTerm')
    member      = models.ForeignKey('mig_main.MemberProfile')
    
class Requirement(models.Model):
    distinction_type    = models.ForeignKey(DistinctionType)
    name                = models.CharField(max_length=30)
    term                = models.ManyToManyField(SemesterType)
    amount_required     = models.PositiveSmallIntegerField()
    event_category      = models.ForeignKey(EventCategory)
    def __unicode__(self):
        terms = ', '.join([unicode(term) for term in self.term.all()])
        return  self.name +' for '+self.distinction_type.name+': '+terms


class ProgressItem(models.Model):
    member              = models.ForeignKey('mig_main.MemberProfile')
    term                = models.ForeignKey('mig_main.AcademicTerm')
    related_event       = models.ForeignKey('event_cal.CalendarEvent',null=True,blank=True)
    event_type          = models.ForeignKey(EventCategory)
    amount_completed    = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0)])
    date_completed      = models.DateField()
    name                = models.CharField('Name/Desciption',max_length = 100) 
    def __unicode__(self):
        return self.member.get_full_name()+': '+unicode(self.amount_completed) +' credit(s) toward '+unicode(self.event_type)+' on '+unicode(self.date_completed) + ' for '+unicode(self.term)
