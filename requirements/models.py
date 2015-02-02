from django.core.cache import cache
from django.core.validators import  RegexValidator,MinValueValidator
from django.db import models
from django.db.models import Q

# Create your models here.


class DistinctionType(models.Model):
    #Electee, Active, DA, PA
    name = models.CharField(max_length = 30)
    status_type = models.ForeignKey('mig_main.Status')
    standing_type = models.ManyToManyField('mig_main.Standing')
    display_order = models.PositiveSmallIntegerField(default=0)
    def __unicode__(self):
        return self.name
    def save(self, *args, **kwargs): 
        super(DistinctionType, self).save(*args, **kwargs) # Call the "real" save() method.
        cache.delete_many(['PROGRESS_TABLE_ACTIVE_DIST','PROGRESS_TABLE_UGRADEL_DIST','PROGRESS_TABLE_GRADEL_DIST'])
    def delete(self, *args, **kwargs): 
        super(DistinctionType, self).delete(*args, **kwargs) # Call the "real" delete() method.
        cache.delete_many(['PROGRESS_TABLE_ACTIVE_DIST','PROGRESS_TABLE_UGRADEL_DIST','PROGRESS_TABLE_GRADEL_DIST'])
    
class SemesterType(models.Model):
    #Summer, Fall, Winter
    name = models.CharField(max_length = 30)
    def __unicode__(self):
        return self.name+' semester'
    def __gt__(self,term2):
        if not hasattr(term2,'name'):
            return True
        if self.name =='Winter':
            return False
        if self.name =='Summer' and term2.name =='Winter':
            return True
        if self.name =='Fall' and term2.name !='Fall':
            return True
        return False
    def __lt__(self,term2):
        if not hasattr(term2,'name'):
            return False
        if self.name =='Fall':
            return False
        if self.name =='Summer' and term2.name =='Fall':
            return True
        if self.name =='Winter' and term2.name !='Winter':
            return True
        return False
    def __eq__(self,term2):
        if not hasattr(term2,'name'):
            return False
        return self.name == term2.name
    def __ne__(self,term2):
        return not self == term2
    def __le__(self,term2):
        return not self > term2
    def __ge__(self,term2):
        return not self < term2
    def __sub__(self,term2):
        if not hasattr(term2,'name'):
            return 0
        res = 0
        if self.name =='Winter':
            res=-2
        elif self.name =='Summer':
            res=-1
        
        if term2.name =='Summer':
            res+=1
        elif term2.name=='Winter':
            res+=2
        return res
        
class EventCategory(models.Model):
    parent_category = models.ForeignKey('self',null=True,blank=True,default=None)
    name            = models.CharField(max_length=30)
    def __unicode__(self):
        return self.name
    def get_children(self,query):
        for child in self.eventcategory_set.all():
            query|=child.get_children(query)
        return query|Q(event_type=self)
    @classmethod
    def flatten_category_tree(cls):
        category_array=[]
        for parentless_category in cls.objects.filter(parent_category=None):
            category_array+=parentless_category.flatten_tree(1)
        return category_array
    def flatten_tree(category,depth):
        category_array=[{'category':category,'depth':depth}]
        for child in category.eventcategory_set.all():
            category_array+=child.flatten_tree(depth+1)
        return category_array

class Requirement(models.Model):
    distinction_type    = models.ForeignKey(DistinctionType)
    name                = models.CharField(max_length=30)
    term                = models.ManyToManyField(SemesterType)
    amount_required = models.DecimalField(max_digits=5,decimal_places=2,default=0.00)
    event_category      = models.ForeignKey(EventCategory)
    def __unicode__(self):
        terms = ', '.join([unicode(term) for term in self.term.all()])
        return  self.name +' for '+self.distinction_type.name+': '+terms
    def save(self, *args, **kwargs):     
        super(Requirement, self).save(*args, **kwargs) # Call the "real" save() method.
        cache.delete_many(['PROGRESS_TABLE_ACTIVE_REQS','PROGRESS_TABLE_UGRADEL_REQS','PROGRESS_TABLE_GRADEL_REQS'])
    def delete(self, *args, **kwargs):     
        super(Requirement, self).delete(*args, **kwargs) # Call the "real" delete() method.
        cache.delete_many(['PROGRESS_TABLE_ACTIVE_REQS','PROGRESS_TABLE_UGRADEL_REQS','PROGRESS_TABLE_GRADEL_REQS'])
    

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
    def save(self, *args, **kwargs):
        super(ProgressItem, self).save(*args, **kwargs) # Call the "real" save() method.
        if self.member.status.name=='Active':
            cache.delete('PROGRESS_TABLE_ACTIVE_ROWS')
        elif self.member.standing.name=='Undergraduate':
            cache.delete('PROGRESS_TABLE_UGRADEL_ROWS')
        else:
            cache.delete('PROGRESS_TABLE_GRADEL_ROWS')
    def delete(self, *args, **kwargs):
        if self.member.status.name=='Active':
            cache.delete('PROGRESS_TABLE_ACTIVE_ROWS')
        elif self.member.standing.name=='Undergraduate':
            cache.delete('PROGRESS_TABLE_UGRADEL_ROWS')
        else:
            cache.delete('PROGRESS_TABLE_GRADEL_ROWS')
        super(ProgressItem, self).delete(*args, **kwargs) # Call the "real" delete() method.