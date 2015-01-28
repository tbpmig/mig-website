import sys
import csv
import os
import re
import calendar
from datetime import datetime,date,timedelta
from decimal import Decimal


from history.models import NonEventProject,NonEventProjectParticipant,ProjectReport,NonEventParticipantAlt,Distinction
from requirements.models import ProgressItem,DistinctionType
from mig_main.models import AcademicTerm,OfficerPosition,Status,UserProfile,MemberProfile
from mig_main.utility import get_previous_full_term

cal_dict = {v:k for k,v in enumerate(calendar.month_name)}
def add_da_pa_status_manually(uniqname,distinction,terms,start_term='Fall',start_year='2014'):
    user = MemberProfile.objects.get(uniqname=uniqname)
    term = AcademicTerm.objects.get(year=start_year,semester_type__name=start_term)
    while terms>user.get_num_terms_distinction(distinction):
        if term < user.init_term:
            print uniqname+': ran out of terms'
            break
        if not Distinction.objects.filter(member=user,term=term,distinction_type=distinction).exists():
            d = Distinction(member=user,term=term,distinction_type=distinction)
            if distinction.name=='Active':
                d.gift='N/A'
            else:
                d.gift='Unknown'
            d.save()
        term=get_previous_full_term(term)
    print 'finished %s %s'%(uniqname,unicode(distinction))
        
        
def add_tutoring_to_project_report(id_num):
    pr = NonEventProject.objects.get(id=id_num)
    term = AcademicTerm.objects.get(semester_type__name='Winter',year=2014)
    related_progress = ProgressItem.objects.filter(event_type__name='Tutoring Hours',term=term).order_by('member').distinct()
    participants = {}
    for progress in related_progress:
        if progress.member in participants:
            participants[progress.member]+=progress.amount_completed
        else:
            participants[progress.member]=progress.amount_completed

    for member in participants:
        nepp=NonEventProjectParticipant(project=pr,participant=member,hours=participants[member])
        nepp.save()

def add_F13_from_csv(file_name):
    print 'function closed, bug off'
    return
    project_name_col        =   1
    project_beg_mon_col     =   2
    project_beg_day_col     =   3
    project_beg_year_col    =   4
    project_end_mon_col     =   5
    project_end_day_col     =   6
    project_end_year_col    =   7
    project_new_col         =   8
    how_many_electees_col   =   9
    how_many_actives_col    =   10
    project_leaders_col     =   11
    project_description_col =   12
    purpose_objectives_col  =   13
    community_col           =   14
    university_col          =   15
    profession_col          =   16
    chapter_col             =   17
    honors_col              =   18
    other_col               =   19
    contact_name_col        =   20
    contact_title_col       =   21
    contact_number_col      =   22
    contact_email_col       =   23
    other_info_col          =   24
    org_hours_col           =   25
    participating_hours_col =   26
    timeframe_col           =   27
    other_group_col         =   28
    which_group_col         =   29
    comments_col            =   30
    were_items_needed_col   =   31
    what_items_where_col    =   32
    cost_col                =   33
    problems_col            =   34
    recommendations_col     =   35
    evaluation_col          =   36
    project_exp_col         =   37
    best_part_col           =   38
    improved_col            =   39
    should_continue_col     =   40
    participants_col        =   41
    relevant_officer_col    =   42
    projectDataReader = csv.reader(open(file_name,'r'), delimiter=',')
    ariel = MemberProfile.objects.get(uniqname='akrose')
    for row in projectDataReader:
        project_name=row[project_name_col]
        if len(project_name)<1:
            continue
        b_month=row[project_beg_mon_col]
        b_day=row[project_beg_day_col]
        b_year=row[project_beg_year_col]
        e_month=row[project_end_mon_col]
        e_day=row[project_end_day_col]
        e_year=row[project_end_year_col]
        start_date = datetime.combine(date(int(b_year),cal_dict[b_month],int(b_day)),datetime.min.time())
        end_date = datetime.combine(date(int(e_year),cal_dict[e_month],int(e_day)),datetime.min.time())
        new_project = True if row[project_new_col]=='Yes' else False
        leaders = row[project_leaders_col].split('\n')
        participants = [part_line.split('|') for part_line in row[participants_col].split('\n')]
        category = ''
        if row[community_col]=='X':
            category='COMM'
        elif row[university_col]=='X':
            category = 'UNIV'
        elif row[profession_col]=='X':
            category = 'PROF'
        elif row[chapter_col]=='X':
            category = 'CHAP'
        else:
            category = 'HON'
        contact_name=row[contact_name_col]
        contact_title=row[contact_title_col]
        contact_number=row[contact_number_col]
        contact_email=row[contact_email_col]
        contact_other_info=row[other_info_col]
        if row[timeframe_col]=='1-2 weeks':
            timeframe=timedelta(days=-7)
        elif row[timeframe_col]=='3-4 weeks':
            timeframe=timedelta(days=-21)
        elif row[timeframe_col]=='5-6 weeks':
            timeframe = timedelta(days=-35)
        else:
            timeframe = timedelta(days=-49)
        other_group=row[which_group_col]
        general_comments = row[comments_col]
        items = row[what_items_where_col]
        cost = float(row[cost_col].replace('$','').replace('~','').replace(',',''))
        evaluation = row[evaluation_col]
        rating = row[project_exp_col]
        description = row[project_description_col]
        purpose = row[purpose_objectives_col]
        org_hours = row[org_hours_col]
        problems = row[problems_col]
        recommendations=row[recommendations_col]
        best_part = row[best_part_col]
        improved = row[improved_col]
        should_continue = True if row[should_continue_col]=='Yes' else False
        officer_name = row[relevant_officer_col]
        f13=AcademicTerm.objects.get(semester_type__name='Fall',year=2013)
        #Create Project Report
        pr = ProjectReport()
        pr.name = project_name
        pr.term=f13
        pr.relation_to_TBP_objectives = purpose
        pr.is_new_event = new_project
        pr.organizing_hours = float(org_hours)
        pr.planning_start_date = start_date+timeframe
        pr.target_audience = category
        pr.contact_name = contact_name
        pr.contact_email = contact_email
        pr.contact_phone_number = contact_number
        pr.contact_title = contact_title
        pr.other_info = contact_other_info
        pr.other_group=other_group
        pr.general_comments = general_comments
        pr.items = items
        pr.cost = cost
        pr.problems_encountered=problems
        pr.recommendations = recommendations
        pr.rating = int(rating)
        pr.best_part = best_part
        pr.opportunity_to_improve = improved
        pr.recommend_continuing = should_continue
        pr.save()
        print 'Project Report ' + project_name +'created and saved'

        # Create Non Event Project        
        nep = NonEventProject()
        nep.project_report=pr
        nep.name = project_name
        nep.description = description
        nep.assoc_officer = OfficerPosition.objects.get(name = officer_name)
        nep.term = f13
        nep.start_date = start_date
        nep.end_date = end_date
        nep.save()
        print 'NEP saved'

        # Add leaders to NEP
        for leader in leaders:
            if len(leader)<1:
                continue
            leader_uniqname = leader.replace(')','').split('(')[1].strip()
            if MemberProfile.objects.filter(uniqname = leader_uniqname):
                nep.leaders.add(MemberProfile.objects.get(uniqname=leader_uniqname))
            else:
                nep.leaders.add(ariel)
        nep.save()
        print 'Leaders added'

        # Add participants
        for participant in participants:
            uniqname = participant[0].replace(')','').split('(')[1].strip()
            if UserProfile.objects.filter(uniqname=uniqname).exists():
                nepp = NonEventProjectParticipant()
                nepp.participant = UserProfile.objects.get(uniqname=uniqname)
                nepp.hours = float(participant[2])
            else:
                nepp = NonEventParticipantAlt()
                nepp.participant_name = participant[0]
                nepp.participant_status = Status.objects.get(name__iexact=participant[1].strip())
                nepp.hours = float(participant[2])
            nepp.project=nep
            nepp.save()
        print 'Completed: %s'%(nep.name)



