from datetime import date
from django.db.models import Q
from django.http import HttpResponse
from history.models import Distinction,Officer
from requirements.models import ProgressItem,DistinctionType,Requirement,EventCategory
from mig_main.models import AcademicTerm,MemberProfile
from mig_main.utility import UnicodeWriter

def get_active_members(term):
    members = MemberProfile.get_actives()
    terms = [term, term.get_previous_full_term()]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term =Q(init_term=term.get_previous_full_term())
    query_officer = Q(officer__in=officer_terms)
    query_alumni = Q(standing__name='Alumni') | Q(expect_grad_date__lt=date.today())
    query = query_officer | ((query_active_status | query_initiated_last_term ) & ~ query_alumni)
    
    return members.filter(query).distinct()
    
    
def get_members_who_graduated():
    members = MemberProfile.get_actives().exclude(standing__name='Alumni')
    
    return members.filter(expect_grad_date__lt=date.today()).distinct()
    
def get_active_members_who_came_to_something(term):
    members = get_active_members(term)
    progress_items = ProgressItem.objects.filter(
                                    term=term,
                                    event_type__name='Meeting Attendance'
    )
    return members.filter(progressitem__in=progress_items).distinct()
    
def get_active_members_only_if_they_come(term):
    members = MemberProfile.get_actives()
    terms = [term, term.get_previous_full_term()]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term =Q(init_term=term.get_previous_full_term())
    query_officer = Q(officer__in=officer_terms)
    query_alumni = Q(standing__name='Alumni') | Q(expect_grad_date__lt=date.today())
    query_all_active = query_officer | ((query_active_status | query_initiated_last_term ) & ~ query_alumni)
    progress_items = ProgressItem.objects.filter(
                                    term=term,
                                    event_type__name='Meeting Attendance'
    )
    query_actives_absent_now = ~Q(progressitem__in=progress_items)
    #figure out actives will gain status if they have the meeting credit
    
    query_inactives_need_meeting = ~query_officer & ~ query_active_status &~query_initiated_last_term &~query_alumni 
    query = (query_all_active & query_actives_absent_now) 
    set1=set(members.filter(query).distinct()[:])
    active_dist = DistinctionType.objects.get(name='Active')
    set2=set(members.filter(query_inactives_need_meeting).distinct()[:]).intersection(set(active_dist.get_actives_with_status(term, temp_active_ok=True)))
    
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
    
def get_quorum_list_elections():
    term = AcademicTerm.get_current_term()
    all_actives = MemberProfile.get_actives()
    electees = MemberProfile.get_electees()
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
    for m in electees:
        writer.writerow([m.first_name,m.last_name,m.uniqname,'Electee','No',''])
    return response
