from django.core.cache import cache
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from mig_main.models import MemberProfile

def saturate_hours(value):
    return min(value, 15)

# Create your models here.
class DistinctionType(models.Model):
    """ This is a type of status that can be achieved (Active, DA, PA, etc.)

    It also includes the concept of completing electee requirements. It serves
    as the end point to which requirements point.
    """
    name = models.CharField(max_length=30)
    status_type = models.ForeignKey('mig_main.Status')
    standing_type = models.ManyToManyField('mig_main.Standing')
    display_order = models.PositiveSmallIntegerField(default=0)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(DistinctionType, self).save(*args, **kwargs)
        cache.delete_many([
                'PROGRESS_TABLE_ACTIVE_DIST',
                'PROGRESS_TABLE_UGRADEL_DIST',
                'PROGRESS_TABLE_GRADEL_DIST'
        ])

    def delete(self, *args, **kwargs):
        super(DistinctionType, self).delete(*args, **kwargs)
        cache.delete_many([
                'PROGRESS_TABLE_ACTIVE_DIST',
                'PROGRESS_TABLE_UGRADEL_DIST',
                'PROGRESS_TABLE_GRADEL_DIST'
        ])

    def get_actives_with_status(self, term, temp_active_ok=False):
        query =  Q(distinction_type=self) & Q(term=term.semester_type)
        requirements = Requirement.objects.filter(query)
        unflattened_reqs = Requirement.package_requirements(requirements)
        active_profiles = MemberProfile.get_actives() 
        actives_with_status = []
        for profile in active_profiles:
            packaged_progress = ProgressItem.package_progress(ProgressItem.objects.filter(member=profile,term=term))
            amount_req = 0;
            amount_has = 0;
            has_dist = self.has_distinction_met(packaged_progress, unflattened_reqs, temp_active_ok)
            if has_dist:
                actives_with_status.append(profile)
        return actives_with_status

    def has_distinction_met(self, progress, sorted_reqs, temp_active_ok=False):
        has_dist = True
        for event_category,data in sorted_reqs.items():
            if event_category in progress:
                if self.name=="Prestigious Active":
                    amount = progress[event_category]['sat']
                else:
                    amount = progress[event_category]['full']

            else:
                amount = 0
            req = data["requirements"].filter(distinction_type=self)
            amount_req = 0
            if req:
                amount_req = req[0].amount_required
                if temp_active_ok and event_category.name == 'Meeting Attendance':
                    amount_req-=1
                if temp_active_ok and event_category.name == 'Voting Meeting Attendance':
                    amount_req=0
            if amount_req > amount:
                return False
            has_dist = has_dist and self.has_distinction_met(progress, data["children"], temp_active_ok)
            if not has_dist:
                return False
        return has_dist


class SemesterType(models.Model):
    """ A type of semester (Fall, Winter, Summer).

    Used mostly for differentiating requirements or also officer terms.
    """
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name+' semester'

    def __gt__(self, term2):
        if not hasattr(term2, 'name'):
            return True
        if self.name == 'Winter':
            return False
        if self.name == 'Summer' and term2.name == 'Winter':
            return True
        if self.name == 'Fall' and term2.name != 'Fall':
            return True
        return False

    def __lt__(self, term2):
        if not hasattr(term2, 'name'):
            return False
        if self.name == 'Fall':
            return False
        if self.name == 'Summer' and term2.name == 'Fall':
            return True
        if self.name == 'Winter' and term2.name != 'Winter':
            return True
        return False

    def __eq__(self, term2):
        if not hasattr(term2, 'name'):
            return False
        return self.name == term2.name

    def __ne__(self, term2):
        return not self == term2

    def __le__(self, term2):
        return not self > term2

    def __ge__(self, term2):
        return not self < term2

    def __sub__(self, term2):
        if not hasattr(term2, 'name'):
            return 0
        res = 0

        if self.name == 'Winter':
            res = -2
        elif self.name == 'Summer':
            res = -1

        if term2.name == 'Summer':
            res += 1
        elif term2.name == 'Winter':
            res += 2
        return res

    def get_previous_type(self):
        if self.name == 'Fall':
            return self.__class__.objects.get(name='Summer')
        if self.name == 'Summer':
            return self.__class__.objects.get(name='Winter')
        if self.name == 'Winter':
            return self.__class__.objects.get(name='Fall')

    def get_previous_full_type(self):
        if self.name == 'Fall':
            return self.__class__.objects.get(name='Winter')
        if self.name == 'Summer':
            return self.__class__.objects.get(name='Winter')
        if self.name == 'Winter':
            return self.__class__.objects.get(name='Fall')

    def get_next_type(self):
        if self.name == 'Fall':
            return self.__class__.objects.get(name='Winter')
        if self.name == 'Summer':
            return self.__class__.objects.get(name='Fall')
        if self.name == 'Winter':
            return self.__class__.objects.get(name='Summer')

    def get_next_full_type(self):
        if self.name == 'Fall':
            return self.__class__.objects.get(name='Winter')
        if self.name == 'Summer':
            return self.__class__.objects.get(name='Fall')
        if self.name == 'Winter':
            return self.__class__.objects.get(name='Fall')


class EventCategory(models.Model):
    """ Requirements are situated around activities that correspond with a
    certain category (service, social, etc.). These are those categories.

    Note that these are typically nested (e.g. tutoring is a type of service).
    Thus these contain a foreignkey to another event category.
    """
    parent_category = models.ForeignKey(
                                'self',
                                null=True,
                                blank=True,
                                default=None
    )
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name

    def get_children(self, query):
        """ Returns a Q object that represents a query to get all of the
        events which correspond to this event category or any of its children.
        """
        for child in self.eventcategory_set.all():
            query |= child.get_children(query)
        return query | Q(event_type=self)

    @classmethod
    def flatten_category_tree(cls):
        """ Returns a nested list of the category tree(s). """
        category_array = []
        for parentless_category in cls.objects.filter(parent_category=None):
            category_array += parentless_category.flatten_tree(1)
        return category_array
    
    def flatten_tree(category, depth):
        """ Helper function for flatten_category_tree. """
        category_array = [{'category': category, 'depth': depth}]
        for child in category.eventcategory_set.all():
            category_array += child.flatten_tree(depth+1)
        return category_array


class Requirement(models.Model):
    """ One of the requirements to attain a certain Distinction.

    Ties together Distinctions and EventCategories. Says how many units/hours
    of a particular category are required for a particular distinction.

    May also vary by semester type (e.g. no Career Fair in Winter)
    """
    distinction_type = models.ForeignKey(DistinctionType)
    name = models.CharField(max_length=30)
    term = models.ManyToManyField(SemesterType)
    amount_required = models.DecimalField(
                                max_digits=5,
                                decimal_places=2,
                                default=0.00
    )
    event_category = models.ForeignKey(EventCategory)

    @classmethod
    def package_requirements(cls, requirements):
        sorted_reqs = {}
        return cls.add_child_reqs(sorted_reqs, requirements, None)
    
    @classmethod
    def add_child_reqs(cls, sorted_reqs, requirements, parent):
        event_categories = EventCategory.objects.filter(parent_category=parent)
        for event_category in event_categories:
            reqs = requirements.filter(event_category=event_category)
            if reqs:
                sorted_reqs[event_category]={"children":cls.add_child_reqs({},requirements,event_category),"requirements":reqs}
        return sorted_reqs

    def __unicode__(self):
        terms = ', '.join([unicode(term) for term in self.term.all()])
        return self.name + ' for ' + self.distinction_type.name + ': ' + terms

    def save(self, *args, **kwargs):
        super(Requirement, self).save(*args, **kwargs)
        cache.delete_many([
                'PROGRESS_TABLE_ACTIVE_REQS',
                'PROGRESS_TABLE_UGRADEL_REQS',
                'PROGRESS_TABLE_GRADEL_REQS'
        ])

    def delete(self, *args, **kwargs):
        super(Requirement, self).delete(*args, **kwargs)
        cache.delete_many([
                'PROGRESS_TABLE_ACTIVE_REQS',
                'PROGRESS_TABLE_UGRADEL_REQS',
                'PROGRESS_TABLE_GRADEL_REQS'
        ])


class ProgressItem(models.Model):
    """ A unit of progress toward satisfying a requirement.

    Ties together members and requirements in a particular term.
    """
    member = models.ForeignKey('mig_main.MemberProfile')
    term = models.ForeignKey('mig_main.AcademicTerm')
    related_event = models.ForeignKey(
                            'event_cal.CalendarEvent',
                            null=True,
                            blank=True
    )
    event_type = models.ForeignKey(EventCategory)
    amount_completed = models.DecimalField(
                            max_digits=5,
                            decimal_places=2,
                            validators=[MinValueValidator(0)]
    )
    date_completed = models.DateField()
    name = models.CharField('Name/Desciption', max_length=100)

    def __unicode__(self):
        return self.member.get_full_name() + ': ' +\
               unicode(self.amount_completed) + ' credit(s) toward ' +\
               unicode(self.event_type) + ' on ' +\
               unicode(self.date_completed) + ' for '+unicode(self.term)

    def save(self, *args, **kwargs):
        super(ProgressItem, self).save(*args, **kwargs)
        if self.member.status.name == 'Active':
            cache.delete('PROGRESS_TABLE_ACTIVE_ROWS')
        elif self.member.standing.name == 'Undergraduate':
            cache.delete('PROGRESS_TABLE_UGRADEL_ROWS')
        else:
            cache.delete('PROGRESS_TABLE_GRADEL_ROWS')

    def delete(self, *args, **kwargs):
        if self.member.status.name == 'Active':
            cache.delete('PROGRESS_TABLE_ACTIVE_ROWS')
        elif self.member.standing.name == 'Undergraduate':
            cache.delete('PROGRESS_TABLE_UGRADEL_ROWS')
        else:
            cache.delete('PROGRESS_TABLE_GRADEL_ROWS')
        super(ProgressItem, self).delete(*args, **kwargs)

    @classmethod
    def package_progress(cls, progress_items):
        packaged_progress={}
        for progress_item in progress_items:
            associated_event_type =progress_item.event_type
            if associated_event_type in packaged_progress.keys():
                packaged_progress[associated_event_type]['full']+=progress_item.amount_completed
                packaged_progress[associated_event_type]['sat']+=saturate_hours(progress_item.amount_completed)
            else:
                packaged_progress[associated_event_type]={'full':0,'sat':0}
                packaged_progress[associated_event_type]['full']=progress_item.amount_completed
                packaged_progress[associated_event_type]['sat']=saturate_hours(progress_item.amount_completed)
            while associated_event_type.parent_category!=None:
                associated_event_type = associated_event_type.parent_category
                if associated_event_type in packaged_progress.keys():
                    packaged_progress[associated_event_type]['full']+=progress_item.amount_completed
                    packaged_progress[associated_event_type]['sat']+=saturate_hours(progress_item.amount_completed)
                else:
                    packaged_progress[associated_event_type]={'full':0,'sat':0}
                    packaged_progress[associated_event_type]['full']=progress_item.amount_completed
                    packaged_progress[associated_event_type]['sat']=saturate_hours(progress_item.amount_completed)
        return packaged_progress
