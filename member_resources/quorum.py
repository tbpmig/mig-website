from time import sleep

from django.core.mail import send_mail
from datetime import date
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from history.models import Distinction, Officer
from requirements.models import (
                    ProgressItem,
                    DistinctionType,
                    Requirement,
                    EventCategory
)
from mig_main.models import AcademicTerm, MemberProfile
from mig_main.utility import UnicodeWriter


def get_active_members(term):
    members = MemberProfile.get_actives()
    terms = [term, term.get_previous_full_term()]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term = Q(init_term=term.get_previous_full_term())
    query_officer = Q(officer__in=officer_terms)
    query_alumni = (Q(standing__name='Alumni') |
                    Q(expect_grad_date__lt=date.today()))
    query = query_officer | (
            (query_active_status | query_initiated_last_term) & ~query_alumni
    )

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


def get_active_members_only_if_they_come(term, is_last_voting_meeting=False):
    members = MemberProfile.get_actives()
    terms = [term, term.get_previous_full_term()]
    officer_terms = Officer.objects.filter(term__in=[term])
    distinctions = Distinction.objects.filter(term__in=terms)
    query_active_status = Q(distinction__in=distinctions)
    query_initiated_last_term = Q(init_term=term.get_previous_full_term())
    query_officer = Q(officer__in=officer_terms)
    query_alumni = (Q(standing__name='Alumni') |
                    Q(expect_grad_date__lt=date.today()))
    query_all_active = query_officer | (
            (query_active_status | query_initiated_last_term) & ~ query_alumni
    )
    progress_items = ProgressItem.objects.filter(
                                    term=term,
                                    event_type__name='Meeting Attendance'
    )
    query_actives_absent_now = ~Q(progressitem__in=progress_items)
    # figure out actives will gain status if they have the meeting credit

    query_inactives_need_meeting = (
        ~query_officer & ~query_active_status & ~query_initiated_last_term & ~query_alumni
    )
    query = (query_all_active & query_actives_absent_now)
    set1 = set(members.filter(query).distinct()[:])
    active_dist = DistinctionType.objects.get(name='Active')
    temp_active_ok = not is_last_voting_meeting
    set2 = set(
            members.filter(
                    query_inactives_need_meeting).distinct()[:]
        ).intersection(
            set(
                active_dist.get_actives_with_status(
                                            term,
                                            temp_active_ok=temp_active_ok
                )
            )
        )

    return list(set1.union(set2))


def get_quorum_list():
    term = AcademicTerm.get_current_term()
    all_actives = MemberProfile.get_actives()
    active_actives = get_active_members(term)
    members_who_graduated = get_members_who_graduated()
    actual_actives = get_active_members_who_came_to_something(term)
    potential_actives = get_active_members_only_if_they_come(term)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="MemberStatus.csv"'

    writer = UnicodeWriter(response)
    writer.writerow([
            'First Name',
            'Last Name',
            'uniqname',
            'Active?',
            'Alumni?',
            'Present'
    ])
    for m in all_actives:
        if m in potential_actives:
            active = 'If present'
        elif m in actual_actives:
            active = 'Yes'
        elif m.standing.name == 'Alumni':
            active = 'Confirm Manually'
        else:
            active = 'No'
        if m in members_who_graduated:
            alum_text = 'Maybe'
        elif m.standing.name == 'Alumni':
            alum_text = 'Yes'
        else:
            alum_text = 'No'
        writer.writerow([
                m.first_name,
                m.last_name,
                m.uniqname,
                active,
                alum_text,
                ''
        ])
    return response


def get_quorum_list_elections():
    term = AcademicTerm.get_current_term()
    all_actives = MemberProfile.get_actives()
    electees = MemberProfile.get_electees()
    active_actives = get_active_members(term)
    members_who_graduated = get_members_who_graduated()
    actual_actives = get_active_members_who_came_to_something(term)
    potential_actives = get_active_members_only_if_they_come(
                                            term,
                                            is_last_voting_meeting=True
    )
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="MemberStatus.csv"'

    writer = UnicodeWriter(response)
    writer.writerow([
            'First Name',
            'Last Name',
            'uniqname',
            'Active?',
            'Alumni?',
            'Present'
    ])
    for m in all_actives:
        if m in potential_actives:
            active = 'If present'
        elif m in actual_actives:
            active = 'Yes'
        elif m.standing.name == 'Alumni':
            active = 'Confirm Manually'
        else:
            active = 'No'
        if m in members_who_graduated:
            alum_text = 'Maybe'
        elif m.standing.name == 'Alumni':
            alum_text = 'Yes'
        else:
            alum_text = 'No'
        writer.writerow([
                m.first_name,
                m.last_name,
                m.uniqname,
                active,
                alum_text,
                ''
        ])
    for m in electees:
        writer.writerow([
                m.first_name,
                m.last_name,
                m.uniqname,
                'Electee',
                'No',
                ''
        ])
    return response

    
def email_active_status(meeting, is_elections):
    term = AcademicTerm.get_current_term()
    all_actives = MemberProfile.get_actives()
    active_actives = get_active_members(term)
    members_who_graduated = get_members_who_graduated()
    actual_actives = get_active_members_who_came_to_something(term)
    potential_actives = get_active_members_only_if_they_come(
                            term,
                            is_last_voting_meeting=is_elections
    )
    body_template = r'''Hi %(member)s,
This is a friendly reminder that we have a critical voting meeting -
%(name)s - %(date)s
in %(location)s and we need to have a quorum of active members
present.
Our records indicate that %(status)s

%(alumni)s

If you believe this to be in error, or especially if you are no longer on
campus, please let us know by emailing tbp-website@umich.edu or by speaking
to the president or website chair at the meeting tonight.

Thanks,
The TBP Website'''
    emailed_people = []
    location = meeting.get_locations()
    if len(location)>0:
        location = location[0]
    else:
        location = 'TBD'
    start_end = meeting.get_start_and_end()
    start = timezone.localtime(start_end['start']).strftime('%A (%b %d) at %I:%M%p')
    start_string = 'this '+start
    event_name = meeting.name
    for m in all_actives:
        print 'emailing ' + m.uniqname+'...'
        sleep(1)
        short_code = 'active'
        status_code = ''
        if m in potential_actives:
            status_text = (' you will be considered active and eligible '
                           'to vote upon attending the meeting. While '
                           'your absence will not count against quorum, '
                           'please be advised that voting meetings are '
                           'required to achieve DA/PA status.')
            short_code = 'conditional active'
        elif m in actual_actives:
            status_text = (' you are an active member. You will be '
                           'eligible to vote at the meeting and will '
                           'count against quorum if you cannot or do not '
                           'attend tonight.')
        elif m.standing.name == 'Alumni':
            continue
        else:
            status_text = (' you are no longer active in the chapter. '
                           'You are welcome to attend the meeting, but '
                           'you will be unable to vote.')
            short_code = 'not active'
            if m in members_who_graduated:
                status_text += (' This may be that you are listed as '
                                'having graduated. Alumni may specially '
                                'request active status, but may not vote '
                                'on candidate election')
                short_code = 'non-active alum'
        if m in members_who_graduated:
            alum_text = ('Our records additionally indicate that you have '
                         'likely graduated but are not yet listed as an '
                         'alumni. If this is the case, please let us know '
                         'and update your website profile accordingly. If '
                         'not please update your expected graduation date '
                         'accordingly. Those listed as alumni will be '
                         'ineligible to vote on candidate election.')
            status_code = 'graduated'
        elif m.standing.name == 'Alumni':
            alum_text = (' Our records have you noted as an alumni. Note '
                         'that regardless of active status, alumni may '
                         'not vote on candidate election or changes to '
                         'the initiation fee.')
            status_code = 'alum'
        else:
            alum_text = ''
        body = body_template % {
                    'member': m.first_name,
                    'status': status_text,
                    'alumni': alum_text,
                    'location': location,
                    'date': start_string,
                    'name': event_name
        }
        emailed_people.append([m.uniqname, short_code, status_code])
        send_mail(
            '[TBP] Voting meeting active status update.',
            body,
            'tbp.mi.g@gmail.com',
            [m.get_email()],
            fail_silently=False
        )
    web_summary_body = 'The following members were emailed:\n\n'
    web_summary_body += '\n'.join(
            ['\t\t'.join(sub_list) for sub_list in emailed_people])
    send_mail(
        '[TBP] Voting meeting active status update - summary.',
        web_summary_body,
        'tbp.mi.g@gmail.com',
        ['tbp-website@umich.edu'],
        fail_silently=False
    )