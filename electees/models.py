from django.db import models
from django.db.models import Q,Count
from django.core.validators import  RegexValidator

from event_cal.models import CalendarEvent
from mig_main.pdf_field import ContentTypeRestrictedFileField,pdf_types
from requirements.models import EventCategory
from mig_main.models import AcademicTerm,MemberProfile,Standing

def electee_stopped_electing(profile):
    profile.still_electing=False
    profile.save()
    future_events = CalendarEvent.objects.filter(eventshift__attendees=profile,completed=False)
    for event in future_events:
        for shift in event.eventshift_set.all():
            shift.attendees.remove(profile)
            shift.save()
    for group in ElecteeGroup.objects.filter(term=AcademicTerm.get_current_term(),members=profile):
        group.members.remove(profile)
        group.save()

def add_group_threshold_pts(grp):
    evts = CalendarEvent.objects.filter(completed=True,term=grp.term)
    num_members = grp.members.all().count()
    service_cat = EventCategory.objects.get(name='Service Hours')
    social_cat = EventCategory.objects.get(name='Social Credits')
    service_query = service_cat.get_children(Q())
    social_query = social_cat.get_children(Q())

    threshold_evts = grp.electeegroupevent_set.filter(~Q(related_event_id=None))
    threshold_evts.delete()
    #service
    for evt in evts.filter(service_query):
        if grp.electeegroupevent_set.filter(related_event_id = evt.id).count()>0:
            continue
        num_attendees = 0
        for group_member in grp.members.all():
            if evt.eventshift_set.filter(attendees=group_member).exists():
                num_attendees+=1
        if num_attendees==num_members:
            grp_pts = grp.electeegroupevent_set.create(description='Threshold Attendance Event: '+evt.name,points = 30,related_event_id=evt.id)
            grp_pts.save()
        elif num_attendees>=num_members/2.0:
            grp_pts = grp.electeegroupevent_set.create(description='Threshold Attendance Event: '+evt.name,points = 15,related_event_id=evt.id)
            grp_pts.save()
    #social
    for evt in evts.filter(social_query):
        if grp.electeegroupevent_set.filter(related_event_id = evt.id).count()>0:
            continue
        num_attendees = 0
        for group_member in grp.members.all():
            if evt.eventshift_set.filter(attendees=group_member).exists():
                num_attendees+=1
        if num_attendees==num_members:
            grp_pts = grp.electeegroupevent_set.create(description='Threshold Attendance Event: '+evt.name,points = 10,related_event_id=evt.id)
            grp_pts.save()
        elif num_attendees>=num_members/2.0:
            grp_pts = grp.electeegroupevent_set.create(description='Threshold Attendance Event: '+evt.name,points = 5,related_event_id=evt.id)
            grp_pts.save()
    grp.electeegroupevent_set.filter(description='half_members_3_socials').delete()
    grp.electeegroupevent_set.filter(description='All_members_3_socials').delete()
    num_w_three = 0
    for group_member in grp.members.all():
        socials_attended = evts.filter(social_query).filter(eventshift__attendees=group_member).distinct().count()
        if socials_attended>=3:
            num_w_three+=1
    if num_w_three == num_members:
        grp_pts = grp.electeegroupevent_set.create(description='All_members_3_socials',points=40)
        grp_pts.save()
    elif num_w_three >=num_members/2.0:
        grp_pts = grp.electeegroupevent_set.create(description='half_members_3_socials',points=20)
        grp_pts.save()


# Create your models here.
class ElecteeGroup(models.Model):
    group_name  = models.CharField('Team Name',max_length=50)   
    leaders     = models.ManyToManyField('mig_main.MemberProfile',
                                         related_name ="electee_group_leaders")
    officers    = models.ManyToManyField('mig_main.MemberProfile',
                                          related_name ="electee_group_officers")
    members     = models.ManyToManyField('mig_main.MemberProfile',
                                          related_name ="electee_group_members")
    points      = models.PositiveSmallIntegerField(default=0)
    term        = models.ForeignKey('mig_main.AcademicTerm')
    @classmethod
    def get_current_leaders(cls):
        current_groups = cls.objects.filter(term=AcademicTerm.get_current_term())
        return MemberProfile.objects.filter(Q(electee_group_leaders__in=current_groups)|Q(electee_group_officers__in=current_groups)).distinct().order_by('last_name','first_name','uniqname')
    def __unicode__(self):
        return unicode(self.term)+": "+self.group_name
    def add_threshold_attendance_points(self):  
        add_group_threshold_pts(self)
    
    def sum_group_points(self):
        evts = self.electeegroupevent_set.all()
        temp_pts = 0
        for evt in evts:
            temp_pts +=evt.points
        self.points = temp_pts
        self.save()
    def get_points(self):
        if self.members.count()>0:
            self.add_threshold_attendance_points()
            self.sum_group_points()
        return self.points
    def get_ranking(self):
        return ElecteeGroup.objects.filter(term=self.term,points__gt=self.points).count()+1

class ElecteeGroupEvent(models.Model):
    electee_group = models.ForeignKey(ElecteeGroup,verbose_name='Electee Team')
    description = models.TextField()
    points      = models.PositiveSmallIntegerField()
    related_event_id = models.PositiveIntegerField(null=True,blank=True,default=None)
   
class ElecteeResourceType(models.Model):
    name = models.CharField(max_length = 128)
    is_packet = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
def get_default_standing():
    return Standing.objects.get(name='Undergraduate').id
class ElecteeResource(models.Model):
    resource_type = models.ForeignKey(ElecteeResourceType)
    standing = models.ForeignKey('mig_main.Standing',default=get_default_standing,null=True,blank=True)
    term = models.ForeignKey('mig_main.AcademicTerm')

    resource_file          = ContentTypeRestrictedFileField(
        upload_to='electee_resources',
        content_types=pdf_types,
        max_upload_size=104857600,
        blank=False
    )

    def __unicode__(self):
        if self.standing:
            standing_string = unicode(self.standing)+' '
        else:
            standing_string = ''
        return standing_string+unicode(self.resource_type)+' for '+unicode(self.term)

class EducationalBackgroundForm(models.Model):
    degree_type=models.CharField(max_length = 16)
    member = models.ForeignKey('mig_main.MemberProfile')
    term = models.ForeignKey('mig_main.AcademicTerm')

class BackgroundInstitution(models.Model):
    form = models.ForeignKey(EducationalBackgroundForm)
    name = models.CharField(max_length=128,verbose_name='Institution Name')
    degree_type = models.CharField(max_length = 16)
    major = models.CharField(max_length = 128)
    degree_start_date = models.DateField()
    degree_end_date = models.DateField()

class SurveyPart(models.Model):
    VISIBILITY_OPTIONS = (
        ('E','Fellow Electees'),
        ('A','Active Members'),
        ('M','All Members'),
        ('R','Only Admins/VPs'),
    )
    title = models.CharField(max_length=128)
    number_of_required_questions = models.PositiveSmallIntegerField(blank=True,null=True)
    display_order = models.PositiveSmallIntegerField(default=1)
    visibility = models.CharField(max_length=1,choices=VISIBILITY_OPTIONS, default='R')
    instructions = models.TextField(blank=True,null=True)
    def __unicode__(self):
        return self.title
    def __gt__(self,part2):
        if not hasattr(part2,'display_order') or not hasattr(part2,'id'):
            return True
        if self.display_order > part2.display_order:
            return True
        if (self.display_order == part2.display_order) and self.id > part2.id:
            return True
        return False
    
    def __lt__(self,part2):
        if not hasattr(part2,'display_order') or not hasattr(part2,'id'):
            return False
        if self.display_order < part2.display_order:
            return True
        if (self.display_order == part2.display_order) and self.id < part2.id:
            return True
        return False
    def __le__(self,part2):
        return not self > part2
    def __ge__(self,part2):
        return not self < part2
class SurveyQuestion(models.Model):
    short_name = models.CharField(max_length=64)
    text = models.TextField()
    part = models.ForeignKey(SurveyPart)
    max_words = models.PositiveSmallIntegerField(blank=True,null=True)
    display_order = models.PositiveSmallIntegerField(default=1)
    
    def __unicode__(self):
        return self.short_name+'('+unicode(self.part)+')'
        
class SurveyAnswer(models.Model):
    term = models.ForeignKey('mig_main.AcademicTerm')
    question = models.ForeignKey(SurveyQuestion)
    submitter = models.ForeignKey('mig_main.MemberProfile')
    answer = models.TextField()
    
    def __unicode__(self):
        return self.submitter.uniqname+'\'s answer to '+unicode(self.question)
        
class ElecteeInterviewSurvey(models.Model):
    term = models.ForeignKey('mig_main.AcademicTerm')
    questions= models.ManyToManyField(SurveyQuestion)
    due_date = models.DateField()
    instructions = models.TextField(blank=True,null=True)
    def __unicode__(self):
        return 'Electee Survey for '+unicode(self.term)
       
    def check_if_electee_completed(self,electee):
        parts = SurveyPart.objects.filter(surveyquestion__in=self.questions.all()).distinct()
        completed = True
        for part in parts:
            num_req = part.number_of_required_questions
            part_answers = SurveyAnswer.objects.filter(submitter=electee,term=self.term,question__part=part).count()
            if (not num_req is None) and part_answers < num_req:
                return False
        if not electee.resume:
            return False
        return True
        
class ElecteeInterviewFollowup(models.Model):
    RECOMMENDATION_CHOICES = (
        ('Y','Recommend'),
        ('M','Not Sure'),
        ('N','Do not recommend'),
        ('X','Missed Interview'),
    )
    
    language_barrier = models.BooleanField(default=False)
    recommendation = models.CharField(max_length=1,choices=RECOMMENDATION_CHOICES)
    comments = models.TextField(blank=True)
    member =models.ForeignKey('mig_main.MemberProfile')
    interview = models.ForeignKey('event_cal.InterviewShift')
    
class ElecteeProcessVisibility(models.Model):
    term = models.ForeignKey('mig_main.AcademicTerm',unique=True)
    followups_visible = models.BooleanField(default=False)
