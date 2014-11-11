from datetime import date
from django.db.models import Q
from django.http import HttpResponse
from mig_main.utility import get_previous_full_term
from history.models import Distinction,Officer
from requirements.models import ProgressItem,DistinctionType,Requirement,EventCategory
from mig_main.models import AcademicTerm,MemberProfile
from mig_main.utility import UnicodeWriter

#TODO: remove duplication
def package_requirements(requirements):
    sorted_reqs={}
    return add_child_reqs(sorted_reqs,requirements,None)
def add_child_reqs(sorted_reqs,requirements,parent):
    event_categories = EventCategory.objects.filter(parent_category=parent)
    for event_category in event_categories:
        reqs = requirements.filter(event_category=event_category)
        if reqs:
            sorted_reqs[event_category]={"children":add_child_reqs({},requirements,event_category),"requirements":reqs}
    return sorted_reqs
def package_progress(progress_items):
    packaged_progress={}
    for progress_item in progress_items:
        associated_event_type =progress_item.event_type
        if associated_event_type in packaged_progress.keys():
            packaged_progress[associated_event_type]+=progress_item.amount_completed
        else:
            packaged_progress[associated_event_type]=progress_item.amount_completed
        while associated_event_type.parent_category!=None:
            associated_event_type = associated_event_type.parent_category
            if associated_event_type in packaged_progress.keys():
                packaged_progress[associated_event_type]+=progress_item.amount_completed
            else:
                packaged_progress[associated_event_type]=progress_item.amount_completed
    return packaged_progress

def has_distinction_met(progress,distinction,sorted_reqs):
    has_dist = True
    for event_category,data in sorted_reqs.items():
        if event_category in progress:
            amount = progress[event_category]
        else:
            amount = 0
        req = data["requirements"].filter(distinction_type=distinction)
        amount_req = 0
        if req:
            amount_req = req[0].amount_required
            if event_category.name=='Meeting Attendance':
                amount_req-=1
        if amount_req>amount:
            return False
        has_dist = has_dist and has_distinction_met(progress,distinction,data["children"])
        if not has_dist:
            return False
    return has_dist
def get_actives_with_status(distinction):
    query =  Q(distinction_type=distinction)& Q(term=AcademicTerm.get_current_term().semester_type)
    requirements = Requirement.objects.filter(query).exclude(event_category__name='Voting Meeting Attendance')
    unflattened_reqs = package_requirements(requirements)
    active_profiles = MemberProfile.get_actives() 
    actives_with_status = []
    for profile in active_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=AcademicTerm.get_current_term()))
        amount_req = 0;
        amount_has = 0;
        has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
        if has_dist:
            actives_with_status.append(profile)
    return actives_with_status

def get_active_members(term):
    members = MemberProfile.get_actives()
    terms = [term, get_previous_full_term(term)]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term =Q(init_term=get_previous_full_term(term))
    query_officer = Q(officer__in=officer_terms)
    query_alumni = Q(standing__name='Alumni') | Q(expect_grad_date__lt=date.today())
    query = query_officer | ((query_active_status | query_initiated_last_term ) & ~ query_alumni)
    
    return members.filter(query).distinct()
    
    
def get_members_who_graduated():
    members = MemberProfile.get_actives().exclude(standing__name='Alumni')
    
    return members.filter(expect_grad_date__lt=date.today()).distinct()
    
def get_active_members_who_came_to_something(term):
    members = get_active_members(term)
    progress_items =ProgressItem.objects.filter(term=term)
    return members.filter(progressitem__in=progress_items).distinct()
    
def get_active_members_only_if_they_come(term):
    members = MemberProfile.get_actives()
    terms = [term, get_previous_full_term(term)]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term =Q(init_term=get_previous_full_term(term))
    query_officer = Q(officer__in=officer_terms)
    query_alumni = Q(standing__name='Alumni') | Q(expect_grad_date__lt=date.today())
    query_all_active = query_officer | ((query_active_status | query_initiated_last_term ) & ~ query_alumni)
    progress_items =ProgressItem.objects.filter(term=term)
    query_actives_absent_now = ~Q(progressitem__in=progress_items)
    #figure out actives will gain status if they have the meeting credit
    
    query_inactives_need_meeting = ~query_officer & ~ query_active_status &~query_initiated_last_term &~query_alumni 
    query = (query_all_active & query_actives_absent_now) 
    set1=set(members.filter(query).distinct()[:])
    set2=set(members.filter(query_inactives_need_meeting).distinct()[:]).intersection(set(get_actives_with_status(DistinctionType.objects.get(name='Active'))))
    
    return list(set1.union(set2))

    
def get_quorum_list():
    term = AcademicTerm.get_current_term()
    all_actives = MemberProfile.get_actives()
    active_actives = get_active_members(term)
    members_who_graduated = get_members_who_graduated()
    actual_actives = get_active_members_who_came_to_something(term)
    potential_actives = get_active_members_only_if_they_come(term)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename="MemberStatus.csv"'

    writer = UnicodeWriter(response)
    writer.writerow([ 'First Name','Last Name','uniqname','Active?','Alumni?','Present'])
    for m in all_actives:
        if m in potential_actives:
            active='If present'
        elif m in actual_actives:
            active='Yes'
        elif m.standing.name=='Alumni':
            active='Confirm Manually'
        else:
            active='No'
        if m in members_who_graduated:
            alum_text = 'Maybe'
        elif m.standing.name=='Alumni':
            alum_text = 'Yes'
        else:
            alum_text='No'
        writer.writerow([m.first_name,m.last_name,m.uniqname,active,alum_text,''])
    return response