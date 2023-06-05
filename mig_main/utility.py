import csv
import codecs
import cStringIO
import os
from datetime import date

from django.db.models import Q
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse


from electees.models import ElecteeGroup, ElecteeProcessVisibility
from elections.models import Election
from event_cal.models import CalendarEvent
from mig_main.models import AcademicTerm, OfficerPosition, MemberProfile
from requirements.models import SemesterType
from history.models import Officer, ProjectReport, OfficerPositionRelationship
from member_resources.models import ProjectLeaderList
from outreach.models import OutreachEventType


def zipdir(path, zipf):
    for root, dirs, files in os.walk(path):
        for f in files:
            zipf.write(os.path.join(root, f))


def get_officer_position_predecessor_helper(officer, term, officer_set):
    links = officer.officer_relationship_successor.exclude(
                id__in=officer_set
        ).exclude(effective_term__gt=term).order_by('-effective_term')
    if links.exists():
        active_links = links.filter(effective_term=links[0].effective_term)
    else:
        active_links = links
    officer_set |= active_links
    for link in active_links:
        officer_set |= get_officer_position_predecessor_helper(
                            link.predecessor,
                            link.effective_term.get_previous_full_term(),
                            officer_set
        )
    return officer_set


def get_officer_positions_predecessors(officers, term=None):
    if term is None:
        term = AcademicTerm.get_current_term()
    officer_set = OfficerPositionRelationship.objects.none()
    for officer in officers:
        officer_set |= get_officer_position_predecessor_helper(
                                    officer,
                                    term,
                                    officer_set
        )
    officer_trace = {}
    for officer in officers:
        officer_trace[officer] = term
    for rel in officer_set.distinct():
        if rel.predecessor in officer_trace:
            officer_trace[rel.predecessor] = max(
                                                rel.effective_term,
                                                officer_trace[rel.predecessor]
            )
        else:
            officer_trace[rel.predecessor] = rel.effective_term
    return officer_trace


def get_project_report_term():
    today = date.today()
    current_term = AcademicTerm.get_current_term()
    this_fall = Q(year=today.year, semester_type__name='Fall')
    last_fall = Q(year=today.year-1, semester_type__name='Fall')
    next_winter = Q(year=today.year+1, semester_type__name='Winter')
    this_winter = Q(year=today.year, semester_type__name='Winter')
    this_summer = Q(year=today.year, semester_type__name='Summer')
    last_summer = Q(year=today.year-1, semester_type__name='Summer')
    if today.month >= 9:
        # the project reports were already turned in, only care about the fall
        return AcademicTerm.objects.filter(
                                    this_fall |
                                    next_winter |
                                    this_summer)
    elif today.month >=5:
        # the project reports might be turned in. Show all
        return AcademicTerm.objects.filter(
                                    this_fall |
                                    next_winter |
                                    this_summer |
                                    this_winter |
                                    last_summer |
                                    last_fall)
    else:  # report not turned in yet
        return AcademicTerm.objects.filter(
                                    this_winter |
                                    last_summer |
                                    last_fall)


def get_previous_officers():
    previous_officers = Officer.objects.filter(term=get_previous_term())
    return MemberProfile.objects.filter(
                            officer__in=previous_officers).distinct()


def get_current_group_leaders():
    current_electee_groups = ElecteeGroup.objects.filter(
                                term=AcademicTerm.get_current_term())
    return MemberProfile.objects.filter(
                        electee_group_leaders__in=current_electee_groups
                    ).distinct()


def get_current_event_leaders():
    current_events = CalendarEvent.objects.filter(
                            term=AcademicTerm.get_current_term())
    return MemberProfile.objects.filter(
                            event_leader__in=current_events).distinct()


def get_message_dict(request):
    error_message = request.session.pop('error_message', None)
    warning_message = request.session.pop('warning_message', None)
    success_message = request.session.pop('success_message', None)
    info_message = request.session.pop('info_message', None)
    return {
        'error_message': error_message,
        'warning_message': warning_message,
        'success_message': success_message,
        'info_message': info_message,
    }


def get_previous_page(request, alternate='home', args=tuple()):
    if 'current_page' in request.session:
        return redirect(request.session['current_page'])
    else:
        if args:
            return redirect(alternate, *args)
        else:
            return redirect(alternate)


def get_dropdowns(user):
    # NOTE: subsub navs will not show in dropdowns but will
    # show in the secondary bar (currently just for member resources).
    # Three levels deep is max supported
    dropdowns = {
            'about': [],
            'event_cal': [],
            'outreach': [],
            'member_resources': [],
            'corporate': [],
            'publications': [],
    }
    # about: currently no permissions dependence
    dropdowns['about'].append({
                    'subnav': 'about',
                    'link_name': 'About',
                    'link': reverse('about:index')
    })
    dropdowns['about'].append({
                    'subnav': 'joining',
                    'link_name': 'Joining',
                    'link': reverse('about:eligibility')
    })
    dropdowns['about'].append({
                    'subnav': 'leadership',
                    'link_name': 'Leadership',
                    'link':
                    reverse('about:leadership')
    })
    dropdowns['about'].append({
                    'subnav': 'bylaws',
                    'link_name': 'Chapter Bylaws',
                    'link': reverse('about:bylaws')
    })

    # event_cal
    dropdowns['event_cal'].append({
                    'subnav': 'gcal',
                    'link_name': 'Google Calendar',
                    'link': reverse('event_cal:index')
    })
    dropdowns['event_cal'].append({
                    'subnav': 'list',
                    'link_name': 'Event List',
                    'link': reverse('event_cal:list')
    })
    dropdowns['event_cal'].append({
                    'subnav': 'my_events',
                    'link_name': 'My Events',
                    'link': reverse('event_cal:my_events')
    })
    if hasattr(user, 'userprofile') and user.userprofile.is_member():
        dropdowns['event_cal'].append({
                    'subnav': 'tutoring_form',
                    'link_name': 'Submit Tutoring Form',
                    'link': reverse('event_cal:submit_tutoring_form')
        })
    if Permissions.can_view_calendar_admin(user):
        dropdowns['event_cal'].append({
                    'subnav': 'admin',
                    'link_name': 'Calendar Admin',
                    'link': reverse('event_cal:calendar_admin')
        })

    # outreach: currently no permissions dependence
    dropdowns['outreach'].append({
                    'subnav': 'index',
                    'link_name': 'Outreach',
                    'link': reverse('outreach:index')
    })
    dropdowns['outreach'].append({
                    'subnav': 'mindset',
                    'link_name': 'MindSET',
                    'link': reverse('outreach:mindset')
    })
    dropdowns['outreach'].append({
                    'subnav': 'tutoring',
                    'link_name': 'Tutoring',
                    'link': reverse('outreach:tutoring')
    })
    for event_type in OutreachEventType.get_active():
        dropdowns['outreach'].append({
                    'subnav': event_type.url_stem,
                    'link_name': event_type.get_tab_name(),
                    'link': reverse('outreach:outreach_event',
                                    args=[event_type.url_stem])
        })

    # electees: subnav of member_resources
    electee_dropdowns = []
    if Permissions.can_manage_electee_progress(user):
        electee_dropdowns.append({
                    'subnav': 'groups',
                    'link_name': 'Manage Electee Teams',
                    'link': reverse('electees:edit_electee_groups')
        })
        electee_dropdowns.append({
                    'subnav': 'members',
                    'link_name': 'Edit Electee Teams\' Members',
                    'link': reverse('electees:edit_electee_group_membership')
        })
        electee_dropdowns.append({
                    'subnav': 'points',
                    'link_name': 'Edit Electee Team Points',
                    'link': reverse('electees:edit_electee_group_points')
        })

    # elections: subnav of member_resources, depends on existing elections
    elections = Election.get_current_elections()
    elections_dropdowns = []
    for election in elections:
        if elections.count() > 1:
            elections_dropdowns.append({
                    'subnav': 'list'+unicode(election.id),
                    'link_name': 'Nomination List (%s)' % (
                                        election.term.get_abbreviation()),
                    'link': reverse('elections:list', args=[election.id])
            })
        elections_dropdowns.append({
                    'subnav': 'my_nominations' + unicode(election.id),
                    'link_name': 'My Nominations (%s)' % (
                                        election.term.get_abbreviation()),
                    'link': reverse('elections:my_nominations',
                                    args=[election.id])
        })

    # member_resources
    if hasattr(user, 'userprofile') and user.userprofile.is_member():
        dropdowns['member_resources'].append({
                    'subnav': 'member_profiles',
                    'link_name': 'Member Profiles',
                    'link': reverse('member_resources:member_profiles')
        })
    else:
        dropdowns['member_resources'].append({
                    'subnav': 'member_profiles',
                    'link_name': 'Members Resources',
                    'link': reverse('member_resources:index')
        })
    if hasattr(user, 'userprofile') and user.userprofile.is_member():
        dropdowns['member_resources'].append({
                    'subnav': 'view_own_progress',
                    'link_name': 'Track My Progress',
                    'link': reverse('member_resources:view_progress',
                                    args=[user.username])
        })
    if Permissions.can_view_more_than_own_progress(user):
        dropdowns['member_resources'].append({
                    'subnav': 'view_others_progress',
                    'link_name': 'View Others\' Progress',
                    'link': reverse('member_resources:view_progress_list')
        })
    if (Permissions.can_manage_misc_reqs(user) or
       Permissions.can_change_requirements(user)):
        dropdowns['member_resources'].append({
                    'subnav': 'misc_reqs',
                    'link_name': 'Membership Admin',
                    'link': reverse('member_resources:view_misc_reqs')
        })
    if hasattr(user, 'userprofile'):
        dropdowns['member_resources'].append({
                    'subnav': 'playground',
                    'link_name': 'TBPlayground',
                    'link': reverse('fora:index')
        })
    dropdowns['member_resources'].append({
                    'subnav': 'history',
                    'link_name': 'Access History',
                    'link': reverse('member_resources:access_history')
    })
    dropdowns['member_resources'].append({
                    'subnav': 'electees',
                    'link_name': 'Electee Resources',
                    'link': reverse('electees:view_electee_groups'),
                    'subsubnav': electee_dropdowns
    })
    dropdowns['member_resources'].append({
                    'subnav': 'elections',
                    'link_name': 'Elections',
                    'link': reverse('elections:index'),
                    'subsubnav': elections_dropdowns
    })
    if Permissions.can_manage_website(user):
        dropdowns['member_resources'].append({
                    'subnav': 'website',
                    'link_name': 'Manage Website',
                    'link': reverse('member_resources:manage_website')
        })

    # corporate
    dropdowns['corporate'].append({
                    'subnav': 'index',
                    'link_name': 'For Companies',
                    'link': reverse('corporate:index')
    })
    dropdowns['corporate'].append({
                    'subnav': 'resumes',
                    'link_name': u'Member R\u00e9sum\u00e9s', # Generates "Member résumés" string
                    'link': reverse('corporate:resumes')
    })

    # publications
    dropdowns['publications'].append({
                    'subnav': 'news',
                    'link_name': 'Blog',
                    'link': reverse('history:index')
    })
    dropdowns['publications'].append({
                    'subnav': 'cornerstone',
                    'link_name': 'The Cornerstone',
                    'link': reverse('history:cornerstone_view')
    })
    dropdowns['publications'].append({
                    'subnav': 'alumni_news',
                    'link_name': 'Alumni Newsletters',
                    'link': reverse('history:alumninews_view')
    })
    if hasattr(user, 'userprofile') and user.userprofile.is_member():
        dropdowns['publications'].append({
                    'subnav': 'project_reports',
                    'link_name': 'Chapter Project Reports',
                    'link': reverse('history:get_project_reports')
        })

    # bookswap
    # currently none
    return dropdowns


def get_quick_links(user):
    quick_links = []
    if not hasattr(user, 'userprofile'):
        return quick_links
    if not user.userprofile.is_member():
        return quick_links
    profile = user.userprofile.memberprofile
    if profile.standing.name != 'Alumni':
        quick_links.append({
                'link': reverse(
                            'member_resources:view_progress',
                            args=(profile.uniqname,)
                        ),
                'link_name': 'Track My Progress'
        })
    positions = Permissions.get_current_officer_positions(user)
    if Permissions.can_add_announcements(user):
        quick_links.append({
                'link_name': 'Add Weekly Announcement',
                'link': reverse('event_cal:add_announcement')
        })
    if Permissions.can_view_more_than_own_progress(user):
        quick_links.append({
                'link_name': 'View Members\' Progress',
                'link': reverse('member_resources:view_progress_list')
        })
    # Pres items-nothing unique
    # VP items
    if positions.filter(
                Q(position__name='Vice President') |
                Q(position__name='Graduate Student Coordinator') |
                Q(position__name='Graduate Student Vice President')).exists():
        quick_links.append({
                    'link_name': 'Member Admin',
                    'link': reverse('member_resources:view_misc_reqs')
        })
        quick_links.append({
                    'link_name': 'Manage Electee Teams',
                    'link': reverse('electees:view_electee_groups')
        })
    # Secretary items - nothing unique
    # Treasurer items
    if positions.filter(position__name='Treasurer').exists():
        quick_links.append({
                    'link_name': 'Manage Dues Payment',
                    'link': reverse('member_resources:manage_dues')
        })
    # Service Officer
    if positions.filter(position__name='Service Coordinator').exists():
        quick_links.append({
                'link_name': 'Manage Project Leaders',
                'link': reverse('member_resources:manage_project_leaders')
        })
    # K-12 Officer,

    # Campus Outreach,

    # Activities - nothing unique
    # Intersociety - nothing unique
    # NI, Corp, EVP, Historian - nothing unique
    # Publicity
    if positions.filter(position__name='Publicity Officer').exists():
        quick_links.append({
                'link_name': 'Generate Weekly Announcements',
                'link': reverse('event_cal:generate_announcements')
        })
    # Membership Officer -- also needs meeting sign-in once that's a thing
    if positions.filter(position__name='Membership Officer').exists():
        quick_links.append({
                'link_name': 'Member Admin',
                'link': reverse('member_resources:view_misc_reqs')
        })
        quick_links.append({
                'link_name': 'View Meeting Surveys',
                'link': reverse('member_resources:view_meeting_feedback')
        })
    # end officer permissions

    if Permissions.can_create_events(user):
        quick_links.append({
                'link_name': 'Add new event to calendar',
                'link': reverse('event_cal:create_event')
        })
    if Permissions.can_upload_minutes(user):
        quick_links.append({
                'link_name': 'Upload Meeting Minutes',
                'link': reverse('member_resources:upload_minutes')
        })
    if Permissions.can_upload_articles(user):
        quick_links.append({
                'link_name': 'Upload Article',
                'link': reverse('history:upload_article')
        })
    if Permissions.can_post_web_article(user):
        quick_links.append({
                'link': reverse('history:index'),
                'link_name': 'Post Web Story'
        })
    return quick_links


class Permissions:
    @classmethod
    def get_profile(cls, user):
        if not hasattr(user, 'userprofile'):
            return None
        if not user.userprofile.is_member():
            return None
        return user.userprofile.memberprofile

    @classmethod
    def can_nominate(cls, user):
        if cls.get_profile(user):
            return True
        return False

    @classmethod
    def get_previous_officer_positions(cls, user):
        profile = cls.get_profile(user)
        if not profile:
            return Officer.objects.none()
        term = AcademicTerm.get_current_term().get_previous_full_term()
        positions = Officer.objects.filter(
                        user=profile,
                        term=term,
                        position__position_type='O'
        )
        return positions

    @classmethod
    def get_current_officer_positions_positions(cls, user):
        return OfficerPosition.objects.filter(
                    officer__in=cls.get_current_officer_positions(user)
                ).distinct()

    @classmethod
    def get_current_officer_positions(cls, user):
        profile = cls.get_profile(user)
        if not profile:
            return Officer.objects.none()
        term = AcademicTerm.get_current_term()
        if term.semester_type.name == 'Summer':
            term = term.get_next_full_term()
        current_positions = Officer.objects.filter(
                                    user=profile,
                                    term=term,
                                    position__position_type='O'
        )
        return current_positions

    @classmethod
    def get_current_chair_positions(cls, user):
        profile = cls.get_profile(user)
        if not profile:
            return Officer.objects.none()
        term = AcademicTerm.get_current_term()
        if term.semester_type.name == 'Summer':
            term = term.get_next_full_term()
        current_positions = Officer.objects.filter(
                                user=profile,
                                term=term,
                                position__position_type='C'
        )
        return current_positions

    @classmethod
    def can_create_events(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        current_chairs = cls.get_current_chair_positions(user)
        if current_chairs.exists():
            return True
        profile = cls.get_profile(user)
        if not profile:
            return False
        if profile.projectleaderlist_set.all().exists():
            return True
        return False

    @classmethod
    def can_delete_events(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Service Coordinator') |
                 Q(position__name='New Initiatives Officer') |
                 Q(position__name='Vice President') |
                 Q(position__name='Activities Officer') |
                 Q(position__name='Graduate Student Vice President') |
                 Q(position__name='Chapter Development Officer'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_edit_event(cls, event, user):
        try:
            if (hasattr(user, 'userprofile') and
               user.userprofile.memberprofile in event.leaders.all()):
                return True
            else:
                return cls.can_delete_events(user)
        except ObjectDoesNotExist:
            return False

    @classmethod
    def can_update_mindset_materials(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Service Coordinator') |
                 Q(position__name='K-12 Outreach Officer') |
                 Q(position__name='Advisor'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def view_officer_meetings_by_default(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_access_project_reports(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        profile = cls.get_profile(user)
        if not profile:
            return False
        if profile.projectleaderlist_set.all().exists():
            return True
        return False

    @classmethod
    def can_view_meeting_feedback(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_add_external_service(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='Graduate Student Coordinator') |
                 Q(position__name='Service Coordinator') |
                 Q(position__name='Vice President') |
                 Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_upload_articles(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Historian') |
                 Q(position__name='New Initiatives Officer') |
                 Q(position__name='Chapter Development Officer'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_add_announcements(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        return current_positions.exists()

    @classmethod
    def can_generate_announcements(cls, user):
        return cls.can_add_announcements(user)

    @classmethod
    def can_upload_minutes(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        current_chairs = cls.get_current_chair_positions(user)
        if current_positions.exists() or current_chairs.exists():
            return True
        else:
            return False

    @classmethod
    def can_post_web_article(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        profile = cls.get_profile(user)
        if profile and profile.projectleaderlist_set.all().exists():
            return True
        else:
            return False

    @classmethod
    def can_approve_web_article(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Publicity Officer'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_view_others_data(cls, user, uniqname2):
        if user.username == uniqname2:
            return True
        profile2 = MemberProfile.objects.filter(uniqname=uniqname2)
        if not profile2.exists():
            return False
        if user.is_superuser:
            return True
        if not hasattr(user, 'userprofile'):
            return False
        if not user.userprofile.is_member():
            return False
        current_positions = cls.get_current_officer_positions(user)
        if profile2[0].status.name == 'Electee':
            query = (Q(position__name='President') |
                     Q(position__name='Vice President') |
                     Q(position__name='Graduate Student Coordinator') |
                     Q(position__name='Graduate Student Vice President'))
            if current_positions.filter(query).exists():
                return True
            else:
                return False
        else:
            query = (Q(position__name='President') |
                     Q(position__name='Vice President') |
                     Q(position__name='Membership Officer') |
                     Q(position__name='Graduate Student Vice President'))
            if current_positions.filter(query).exists():
                return True
            else:
                return False

    @classmethod
    def can_view_others_progress(cls, user, uniqname2):
        if user.username == uniqname2:
            return True
        profile2 = MemberProfile.objects.filter(uniqname=uniqname2)
        if not profile2.exists():
            return False
        if user.is_superuser:
            return True
        if not hasattr(user, 'userprofile'):
            return False
        if not user.userprofile.is_member():
            return False
        current_positions = cls.get_current_officer_positions(user)
        if profile2[0].status.name == 'Electee':
            query = (Q(position__name='President') |
                     Q(position__name='Vice President') |
                     Q(position__name='Graduate Student Coordinator') |
                     Q(position__name='Graduate Student Vice President'))
            if current_positions.filter(query).exists():
                return True
            elif ElecteeGroup.objects.filter(
                        members=profile2[0],
                        leaders=user.userprofile.memberprofile).exists():
                return True
            elif ElecteeGroup.objects.filter(
                        members=profile2,
                        officers=user.userprofile.memberprofile).exists():
                return True
            else:
                return False
        else:
            query = (Q(position__name='President') |
                     Q(position__name='Vice President') |
                     Q(position__name='Membership Officer') |
                     Q(position__name='Graduate Student Vice President'))
            if current_positions.filter(query).exists():
                return True
            else:
                return False

    @classmethod
    def can_view_more_than_own_progress(cls, user):
        if user.is_superuser:
            return True
        if (not hasattr(user, 'userprofile') or
           not user.userprofile.is_member()):
            return False
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Vice President') |
                 Q(position__name='Graduate Student Coordinator') |
                 Q(position__name='Membership Officer') |
                 Q(position__name='Graduate Student Vice President'))
        query2 = (Q(leaders=user.userprofile.memberprofile) |
                  Q(officers=user.userprofile.memberprofile))
        if current_positions.filter(query).exists():
            return True
        elif ElecteeGroup.objects.filter(query2).exists():
                return True
        else:
            return False

    @classmethod
    def project_reports_you_can_view(cls, user):
        terms = get_project_report_term()
        if user.is_superuser:
            return ProjectReport.objects.filter(
                        term__in=terms).distinct().order_by('name')
        current_positions = cls.get_current_officer_positions(user)
        previous_positions = cls.get_previous_officer_positions(user)
        if (current_positions.filter(position__name='Secretary').exists() or
           previous_positions.filter(position__name='Secretary').exists()):
            return ProjectReport.objects.filter(
                                term__in=terms).distinct().order_by('name')
        profile = cls.get_profile(user)
        if not profile:
            return ProjectReport.objects.none()
        query = Q()
        events = CalendarEvent.objects.filter(term__in=terms).filter(
                                                ~Q(project_report=None))
        for position in current_positions:
            query = query | Q(assoc_officer=position.position)
        query = query | Q(leaders=profile)
        events = events.filter(query)
        project_reports = ProjectReport.objects.filter(
                                calendarevent__in=events).distinct()
        return project_reports.order_by('name')

    @classmethod
    def profiles_you_can_view(cls, user):
        if user.is_superuser:
            return MemberProfile.get_members()
        current_positions = cls.get_current_officer_positions(user)
        query_all = (Q(position__name='President') |
                     Q(position__name='Vice President') |
                     Q(position__name='Graduate Student Vice President'))
        query_actives = Q(position__name='Membership Officer')
        query_electees = Q(position__name='Graduate Student Coordinator')
        query_electee_groups = (Q(leaders=user.userprofile.memberprofile) |
                                Q(officers=user.userprofile.memberprofile))
        query_out = MemberProfile.objects.none()
        if current_positions:
            if current_positions.filter(query_all).exists():
                return MemberProfile.get_members()
            if current_positions.filter(query_actives).exists():
                query_out = query_out | MemberProfile.get_actives()
            if current_positions.filter(query_electees).exists():
                query_out = query_out | MemberProfile.get_electees()

        electee_groups_led = ElecteeGroup.objects.filter(
                                query_electee_groups
                            ).filter(term=AcademicTerm.get_current_term())
        for electee_group in electee_groups_led:
            query_out = query_out | electee_group.members.all()

        return query_out

    @classmethod
    def can_add_leadership_credit(cls, user):
        if user.is_superuser:
            return True
        if cls.can_manage_active_progress(user):
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_other_people = Q(position__name='Service Coordinator')
        if current_positions.filter(query_other_people).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_active_progress(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_actives = (Q(position__name='President') |
                         Q(position__name='Vice President') |
                         Q(position__name='Membership Officer') |
                         Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query_actives).exists():
            return True
        else:
            return False
    
    @classmethod
    def can_download_active_status(cls, user):
        if cls.can_manage_active_progress(user):
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_actives = Q(position__name='Secretary')
        if current_positions.filter(query_actives).exists():
            return True
        else:
            return False
    
    @classmethod
    def can_manage_electee_progress(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_electees = (Q(position__name='President') |
                          Q(position__name='Vice President') |
                          Q(position__name='Graduate Student Coordinator') |
                          Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query_electees).exists():
            return True
        else:
            return False

    @classmethod
    def can_add_electee_members(cls, user):
        if cls.can_manage_electee_progress(user):
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_add_electees = Q(position__name='Secretary')
        if current_positions.filter(query_add_electees).exists():
            return True
        return False

    @classmethod
    def can_change_grad_electee_requirements(cls, user):
        return cls.can_manage_electee_progress(user)

    @classmethod
    def can_process_project_reports(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        previous_positions = cls.get_previous_officer_positions(user)
        query = Q(position__name='Secretary')
        if current_positions.filter(query).exists():
            return True
        if previous_positions.filter(query).exists():
            return True
        return False

    @classmethod
    def can_change_ugrad_electee_requirements(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_positions = (Q(position__name='President') |
                           Q(position__name='Vice President'))
        if current_positions.filter(query_positions).exists():
            return True
        else:
            return False

    @classmethod
    def can_change_active_requirements(cls, user):
        return cls.can_manage_active_progress(user)

    @classmethod
    def can_change_requirements(cls, user):
        return (cls.can_change_active_requirements(user) or
                cls.can_change_ugrad_electee_requirements(user) or
                cls.can_change_grad_electee_requirements(user))

    @classmethod
    def can_manage_misc_reqs(cls, user):
        return (cls.can_manage_membership(user) or
                cls.can_manage_finances(user) or
                cls.can_manage_electee_paperwork(user) or
                cls.can_approve_tutoring(user) or
                cls.can_add_leadership_credit(user) or
                cls.can_view_background_forms(user))

    @classmethod
    def can_approve_tutoring(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = (Q(position__name='President') |
                      Q(position__name='Service Coordinator') |
                      Q(position__name='Campus Outreach Officer'))
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_finances(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = (Q(position__name='President') |
                      Q(position__name='Treasurer'))
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_electee_paperwork(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = (Q(position__name='President') |
                      Q(position__name='Vice President') |
                      Q(position__name='Graduate Student Coordinator') |
                      Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False

    @classmethod
    def can_view_background_forms(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_forms = (Q(position__name='President') |
                       Q(position__name='Secretary') |
                       Q(position__name='Vice President') |
                       Q(position__name='Graduate Student Coordinator') |
                       Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query_forms).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_membership(cls, user):
        return (cls.can_manage_project_leaders(user) or
                cls.can_add_electee_members(user) or
                cls.can_manage_active_progress(user) or
                cls.can_manage_officers(user))

    @classmethod
    def can_manage_project_leaders(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_manage_officers(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_officers = (Q(position__name='President') |
                          Q(position__name='Website Officer'))
        if current_positions.filter(query_officers).exists():
            return True
        return False

    @classmethod
    def can_change_website_term(cls, user):
        return user.is_superuser

    @classmethod
    def can_manage_website(cls, user):
        return user.is_superuser
        
    @classmethod
    def can_manage_bylaws(cls, user):
        return user.is_superuser

    @classmethod
    def can_view_pending_events(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Secretary') |
                 Q(position__name='Service Coordinator'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_view_missing_reports(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Secretary') |
                 Q(position__name='Service Coordinator'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_edit_corporate_page(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Corporate Relations Officer') |
                 Q(position__name='Professional Development Officer') |
                 Q(position__name='External Vice President'))
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_add_corporate_contact(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        else:
            return False

    @classmethod
    def can_add_company(cls, user):
        if user.is_superuser:
            return True
        p = cls.get_profile(user)
        if not p:
            return False
        if p.is_member():
            return True
        return False

    @classmethod
    def can_add_event_photo(cls, user):
        if user.is_superuser:
            return True
        p = cls.get_profile(user)
        if not p:
            return False
        if p.is_member():
            return True
        return False

    @classmethod
    def can_complete_electee_survey(cls, user):
        p = cls.get_profile(user)
        if not p:
            return False
        if not p.is_member():
            return False
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Vice President') |
                 Q(position__name='Graduate Student Vice President'))
        if current_positions.filter(query).exists():
            return True
        if p.memberprofile.status.name == 'Electee':
            return True
        return False

    @classmethod
    def can_view_interview_pairings(cls, user):
        p = cls.get_profile(user)
        if not p:
            return False
        if not p.is_member():
            return False
        else:
            return True

    @classmethod
    def can_see_follow_up(cls, user):
        p = cls.get_profile(user)
        if not p:
            return False
        if not p.is_member():
            return False
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        # switch flipped part
        try:
            vis = ElecteeProcessVisibility.objects.get(
                        term=AcademicTerm.get_current_term()
            )
            if vis.followups_visible and p.is_active():
                return True
            return False
        except ObjectDoesNotExist:
            return False
        return False

    @classmethod
    def can_view_calendar_admin(cls, user):
        return (cls.can_add_event_photo(user) or
                cls.can_create_events(user) or
                cls.can_add_announcements(user) or
                cls.can_generate_announcements(user))

    @classmethod
    def can_create_thread(cls, user):
        if (not hasattr(user, 'userprofile') or
           not user.userprofile.is_member()):
            return False
        return True

    @classmethod
    def can_create_forum(cls, user):
        if not cls.can_create_thread(user):
            return False
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_manage_background_checks(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Service Coordinator') |
                 Q(position__name='K-12 Outreach Officer'))
        if current_positions.filter(query).exists():
            return True
        return False

    @classmethod
    def can_view_demographics(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = (Q(position__name='President') |
                 Q(position__name='Membership Officer'))
        if current_positions.filter(query).exists():
            return True
        return False

    @classmethod
    def can_manage_committees(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_process_bookswap(cls, user):
        if user.is_superuser:
            return True
        # current_positions = cls.get_current_officer_positions(user)
        # if current_positions.exists():
            # return True
        return False


class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8-sig", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
