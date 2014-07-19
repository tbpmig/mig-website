from django.db.models import Count

from history.models import Distinction
from mig_main.default_values import get_current_term
from mig_main.models import MemberProfile,Major,Status,Standing,AcademicTerm
from mig_main.utility import get_previous_full_term
from requirements.models import ProgressItem,DistinctionType,SemesterType


def get_members(init_term=None, include_electees=True,include_stopped_electing=False,include_actives=True,include_grads=True,include_ugrads=True,include_alums=False,only_around=False,only_active_status=False,only_da=False,only_pa=False):
    members = MemberProfile.objects.all()

    #handle status partitions
    if not include_electees:
        members=members.exclude(status__name='Electee')
    elif not include_stopped_electing:
        members=members.exclude(still_electing=False,status__name='Electee')
    if not include_actives:
        members=members.exclude(status__name='Active')
    #handle standing partitions
    if not include_grads:
        members=members.exclude(standing__name="Graduate")
    if not include_ugrads:
        members=members.exclude(standing__name='Undergraduate')
    if not include_alums:
        members=members.exclude(standing__name='Alumni')
    last_two_terms = [get_current_term(), get_previous_full_term(get_current_term())]
    if only_around:
        recent_progress=ProgressItem.objects.filter(term__in=last_two_terms)
        members=members.filter(progressitem__in=recent_progress)
    if only_active_status:
        recent_active = Distinction.objects.filter(term__in=last_two_terms,distinction_type__name='Active')
        members=members.filter(distinction__in=recent_active)
    if only_da:
        recent_active = Distinction.objects.filter(term__in=last_two_terms,distinction_type__name='Distinguished Active')
        members=members.filter(distinction__in=recent_active)
    if only_pa:
        recent_active = Distinction.objects.filter(term__in=last_two_terms,distinction_type__name='Prestigious Active')
        members=members.filter(distinction__in=recent_active)
    if init_term:
        members=members.filter(init_term=init_term,init_chapter__state='MI',init_chapter__letter='G')

    return members.distinct()
def get_distribution(cls,**kwargs):
    members = get_members(**kwargs)
    return cls.objects.filter(memberprofile__in=members).annotate(num_members=Count('memberprofile'))

def get_major_distribution(**kwargs):
    return get_distribution(Major,**kwargs)

def get_gender_distribution(**kwargs):
    members = get_members(**kwargs)
    genders= {}
    genders['Male']=members.filter(gender='M').count()
    genders['Female']=members.filter(gender='F').count()
    genders['Other']=members.filter(gender__contains='O').count()
    return genders

def get_status_distribution(**kwargs):
    return get_distribution(Status,**kwargs)

def get_standing_distribution(**kwargs):
    return get_distribution(Standing,**kwargs)

def get_distinction_distribution(**kwargs):
    term = kwargs.pop('term',None)
    members=get_members(**kwargs)
    distinctions = Distinction.objects.filter(member__in=members)
    if term:
        distinctions=distinctions.filter(term=term)
        
    return DistinctionType.objects.filter(distinction__in=distinctions).annotate(num_members=Count('distinction'))

def get_year_when_join_distribution(**kwargs):
    distribution = {'sophomore':0,'junior':0,'senior':0}
    kwargs['include_grads']=False
    kwargs['include_ugrads']=True
    
    members=get_members(**kwargs)
    for member in members:
        
        if member.expect_grad_date.month>6:
            grad_term=SemesterType.objects.get(name='Fall')
            #Winter grad
            pass
        else:
            #Spring grad
            grad_term = SemesterType.objects.get(name='Winter')
        year_diff = member.expect_grad_date.year-member.init_term.year
        term_diff = grad_term-member.init_term.semester_type
        terms_diff = 3*year_diff+term_diff
        if terms_diff >=0 and terms_diff<=2:
            distribution['senior']+=1
        elif terms_diff>2 and terms_diff<=5:
            distribution['junior']+=1
        elif terms_diff>5 and terms_diff<=8:
            distribution['sophomore']+=1
    return distribution

