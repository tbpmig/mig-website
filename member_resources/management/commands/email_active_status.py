from time import sleep

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from member_resources.quorum import (
        get_active_members,
        get_members_who_graduated,
        get_active_members_who_came_to_something,
        get_active_members_only_if_they_come,
)

from mig_main.models import MemberProfile, AcademicTerm


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--elections',
            action='store_true',
            dest='is_elections',
            default=False,
            help='Specify that the email is for the elections meeting.'
        )

    def handle(self, *args, **options):
        term = AcademicTerm.get_current_term()
        all_actives = MemberProfile.get_actives()
        active_actives = get_active_members(term)
        members_who_graduated = get_members_who_graduated()
        actual_actives = get_active_members_who_came_to_something(term)
        potential_actives = get_active_members_only_if_they_come(term,is_last_voting_meeting=options['is_elections'])
        body_template = r'''Hi %(member)s,
This is a friendly reminder that we have a critical voting meeting tomorrow
(Tuesday) at 6:30pm in 1013 Dow and we need to have a quorum of active members
present.
Our records indicate that %(status)s

%(alumni)s

If you believe this to be in error, or especially if you are no longer on
campus, please let us know by emailing tbp-website@umich.edu or by speaking
to the president or website chair at the meeting tonight.

Thanks,
The TBP Website'''
        emailed_people = []
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
                        'alumni': alum_text
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
