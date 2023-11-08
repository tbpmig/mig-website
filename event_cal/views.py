# Create your views here.
from datetime import datetime, date, timedelta
import re

from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django import forms
from django.forms.models import modelformset_factory, modelform_factory
from django.db.models import Min, Q

from django_ajax.decorators import ajax

from mig_main import messages
from event_cal.forms import (
                AddProjectReportForm,
                BaseEventPhotoForm,
                BaseEventPhotoFormAlt,
                BaseAnnouncementForm,
                CompleteEventFormSet,
                CompleteFixedProgressEventFormSet,
                BaseEventForm,
                EventEmailForm,
                EventFilterForm,
                EventShiftEditFormset,
                EventShiftFormset,
                InterviewShiftFormset,
                MeetingSignInForm,
                MultiShiftFormset,
)
from event_cal.models import (
                AnnouncementBlurb,
                CalendarEvent,
                CarpoolPerson,
                EventClass,
                EventPhoto,
                EventShift,
                GoogleCalendar,
                InterviewPairing,
                InterviewShift,
                MeetingSignIn,
                MeetingSignInUserData,
                UserCanBringPreferredItem,
                WaitlistSlot,
)
from history.models import (
                BackgroundCheck,
                NonEventProject,
                Officer,
                ProjectReport,
)
from mig_main.models import (
                AcademicTerm,
                MemberProfile,
                OfficerPosition,
                PREFERENCES,
                UserPreference,
                UserProfile,
)
from mig_main.utility import get_previous_page, Permissions, get_message_dict
from outreach.models import TutoringRecord
from requirements.models import ProgressItem, EventCategory

from event_cal.gcal_functions import (
                initialize_gcal,
                process_auth,
                get_credentials,
)


NUMBER_OR_NUMERAL = '(^(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$)|^[0-9]+.?[0-9]*$'

GCAL_USE_PREF = [d for d in PREFERENCES
                 if d.get('name') == 'google_calendar_add'][0]
GCAL_ACCT_PREF = [d for d in PREFERENCES
                  if d.get('name') == 'google_calendar_account'][0]


def notify_waitlist_move(event, shift, profile):
    carpool_text = ''
    if event.needs_carpool:
        carpool_text = ('The event is listed as needing a carpool, please '
                        'visit the event page to sign up for the carpool')
    start_time = timezone.localtime(shift.start_time)
    body = r'''Hi %(name)s,

This is an automated notice that you have been moved off of the waitlist for
the event: %(event)s and have automatically been added to the list of
attendees.
Your shift is listed as starting at %(start_time)s, so plan accordingly.
%(carpool)s

If you no longer plan to attend the event, please unsign-up so that another
person may take your spot.
The event is viewable at: https://tbp.engin.umich.edu%(link)s

Thanks,
The TBP Website''' % {
        'name': profile.get_firstlast_name(),
        'event': event.name,
        'start_time': start_time.strftime(
                                "%I:%M %p on %A, %B %d, %Y"
        ),
        'carpool': carpool_text,
        'link': reverse('event_cal:event_detail', args=(event.id,)),
    }

    send_mail(
        '[TBP] You\'ve been moved off an event waitlist.',
        body,
        'tbp.mi.g@gmail.com',
        [profile.get_email()],
        fail_silently=False
    )


def organize_shifts_interview(shifts, is_two_part):
    if is_two_part:
        times = sorted(
                    set(
                        [timezone.localtime(shift.first_shift.start_time)
                         for shift in shifts]
                    )
        )
        locations = sorted(
                    set(
                        [shift.first_shift.location.replace(
                                '(Part 1)',
                                ''
                        ).replace(
                                '(Part 2)',
                                ''
                        ) for shift in shifts]
                    )
        )
        organized_shifts = [
            {
                'time': time,
                'locations': [None for location in locations]
            } for time in times
        ]

    else:
        times = sorted(
                set(
                    [timezone.localtime(shift.start_time) for shift in shifts]
                )
        )
        locations = sorted(
            set(
                [shift.location.replace(
                                '(Part 1)',
                                ''
                ).replace(
                    '(Part 2)',
                    ''
                ).lstrip() for shift in shifts]
            )
        )
        organized_shifts = [
            {
                'time': time,
                'locations': [None for location in locations]
            }
            for time in times
        ]
    for time_count, time in enumerate(times):
        for location_count, location in enumerate(locations):
            if is_two_part:
                shift = shifts.filter(
                            first_shift__start_time=time,
                            first_shift__location__contains=location,
                )
            else:
                shift = shifts.filter(
                            start_time=time,
                            location__contains=location,
                )
            if shift:
                organized_shifts[time_count]['locations'][location_count] = shift[0]
                if is_two_part:
                    organized_shifts[time_count]['end_time'] = shift[0].second_shift.end_time
                else:
                    organized_shifts[time_count]['end_time'] = shift[0].end_time
    return (organized_shifts, locations)


def add_user_to_shift(profile, shift):
    shift.attendees.add(profile)
    gcal_pref = UserPreference.objects.filter(
                        user=profile,
                        preference_type='google_calendar_add'
    )
    if gcal_pref.exists():
        use_cal_pref = gcal_pref[0].preference_value
    else:
        use_cal_pref = GCAL_USE_PREF['default']
    if use_cal_pref == 'always':
        email_pref = UserPreference.objects.filter(
                                    user=profile,
                                    preference_type='google_calendar_account'
        )
        if email_pref.exists():
            cal_email_pref = email_pref[0].preference_value
        else:
            cal_email_pref = GCAL_ACCT_PREF['default']
        if (cal_email_pref == 'umich' or
           not profile.is_member() or
           not profile.memberprofile.alt_email):
            email_to_use = profile.uniqname+'@umich.edu'
        else:
            email_to_use = profile.memberprofile.alt_email
        shift.add_attendee_to_gcal(profile.get_firstlast_name(), email_to_use)


def remove_user_from_shift(profile, shift):
    shift.attendees.remove(profile)
    email_pref = UserPreference.objects.filter(
                        user=profile,
                        preference_type='google_calendar_account'
    )
    if email_pref.exists():
        cal_email_pref = email_pref[0].preference_value
    else:
        cal_email_pref = GCAL_ACCT_PREF['default']
    if (cal_email_pref == 'umich' or
       not profile.is_member() or
       not profile.memberprofile.alt_email):
        email_to_use = profile.uniqname+'@umich.edu'
    else:
        email_to_use = profile.memberprofile.alt_email
    shift.delete_gcal_attendee(email_to_use)


def get_permissions(user):
    return {'can_edit_reports': Permissions.can_process_project_reports(user)}


def get_common_context(request):
    upcoming_html = cache.get('upcoming_events_html', None)
    tz_now = timezone.localtime(timezone.now())
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        gcal_pref = UserPreference.objects.filter(
                    user=profile,
                    preference_type='google_calendar_add'
        )
        if gcal_pref.exists():
            use_cal_pref = gcal_pref[0].preference_value
        else:
            use_cal_pref = GCAL_USE_PREF['default']
        show_manual_add_gcal_button = (use_cal_pref != 'always')
    else:
        show_manual_add_gcal_button = False
    if not upcoming_html:
        upcoming_html = loader.render_to_string(
                    'event_cal/upcoming_events.html',
                    {
                        'upcoming_events': CalendarEvent.get_upcoming_events(),
                        'now': tz_now
                    }
        )
        cache.set('upcoming_events_html', upcoming_html)
    context_dict = get_message_dict(request)
    context_dict.update({
        'request': request,
        'now': tz_now,
        'upcoming_events': upcoming_html,
        'edit_page': False,
        'main_nav': 'cal',
        'show_manual_add_gcal_button': show_manual_add_gcal_button,
    })
    return context_dict


# VIEWS
def index(request):
    request.session['current_page'] = request.path
    template = loader.get_template('event_cal/calendar.html')
    gcals = GoogleCalendar.objects.filter(~Q(name='Office Hours Calendar'))
    if not Permissions.view_officer_meetings_by_default(request.user):
        gcals = gcals.filter(~Q(name='Officer Calendar'))
    context_dict = {
        'google_cals': gcals,
        'office_hours_cal': GoogleCalendar.objects.filter(
                                    name='Office Hours Calendar'
        ),
        'subnav': 'gcal',
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


@login_required
def meeting_sign_in(request, shift_id):
    # XXX kldebug
    from django.db import connection
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    sign_in_sheets = MeetingSignIn.objects.filter(event=event)
    current_tz = timezone.get_current_timezone()
    now = timezone.localtime(timezone.now())
    if sign_in_sheets:
        sign_in_sheet = sign_in_sheets[0]
    else:
        sign_in_sheet = None

    if not shift.can_sign_in():
        if not event.use_sign_in:
            request.session['error_message'] = ('Sign-in not available for '
                                                'this event')
            return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(unicode(event.id),)
            )
        elif shift.is_full():
            request.session['error_message'] = ('You cannot sign-in; the '
                                                'event is full')
            return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(unicode(event.id),)
            )
        else:
            request.session['error_message'] = ('You can only sign-in during '
                                                'the event')
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(unicode(event.id),)
            )

    if not hasattr(request.user, 'userprofile'):
        request.session['error_message'] = ('You must create a profile before '
                                            'signing in to a meeting')
        return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(unicode(event.id),)
        )
    elif not request.user.userprofile.is_member and event.members_only:
        request.session['error_message'] = 'Sorry, this event is members-only'
        return get_previous_page(
                    request,
                    alternate='event_cal:event_detail',
                    args=(unicode(event.id),)
        )
    else:
        profile = request.user.userprofile
        if shift.ugrads_only and not profile.is_ugrad():
            request.session['error_message'] = 'Shift is for undergrads only'
            return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(unicode(event.id),)
            )
        elif shift.grads_only and not profile.is_grad():
            request.session['error_message'] = 'Shift is for grads only'
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(unicode(event.id),)
            )
        elif shift.electees_only and not profile.is_electee():
            request.session['error_message'] = 'Shift is for electees only'
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(unicode(event.id),)
            )
        elif shift.actives_only and not profile.is_active():
            request.session['error_message'] = 'Shift is for actives only'
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(unicode(event.id),)
            )
        if request.method == 'POST':
            if not sign_in_sheet:
                form = MeetingSignInForm(request.POST)
            else:
                sign_in_sheet = sign_in_sheets[0]
                form = MeetingSignInForm(
                            request.POST,
                            question_text=sign_in_sheet.quick_question
                )
            if form.is_valid():
                submitted_code = form.cleaned_data['secret_code']
                if (not sign_in_sheet or
                   submitted_code == sign_in_sheet.code_phrase):
                    is_member = profile.is_member()
                    event_attendees = event.get_attendees_with_progress()
                    if (is_member and
                       profile.memberprofile not in event_attendees):
                        if sign_in_sheet:
                            user_data = MeetingSignInUserData(
                                            meeting_data=sign_in_sheet,
                                            question_response='',
                                            free_response='',
                            )
                            if 'quick_question' in form.cleaned_data:
                                q_resp = form.cleaned_data['quick_question']
                                user_data.question_response = q_resp
                            if 'free_response' in form.cleaned_data:
                                free_resp = form.cleaned_data['free_response']
                                user_data.free_response = free_resp
                                if not user_data.free_response:
                                    user_data.free_response = 'no response'
                            user_data.save()
                        time_d = shift.end_time-shift.start_time
                        hours = time_d.seconds/3600.0
                        if event.is_fixed_progress():
                            hours = 1
                        p = ProgressItem(
                                member=profile.memberprofile,
                                term=AcademicTerm.get_current_term(),
                                amount_completed=hours,
                                event_type=event.event_type,
                                related_event=event,
                                date_completed=date.today(),
                                name=event.name
                        )
                        p.save()
                        request.session['success_message'] = ('You were signed'
                                                              ' in '
                                                              'successfully')
                    elif profile.is_member():
                        request.session['warning_message'] = ('You were '
                                                              'already signed '
                                                              'in')
                    shift.attendees.add(profile)
                    print connection.queries #XXX kldebug
                    return get_previous_page(
                                request,
                                alternate='event_cal:event_detail',
                                args=(unicode(event.id),)
                    )
                else:
                    request.session['error_message'] = ('The meeting\'s secret'
                                                        ' code was wrong. You '
                                                        'were not signed in.')
            else:
                request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
        else:
            if not sign_in_sheet:
                form = MeetingSignInForm()
            else:
                sign_in_sheet = sign_in_sheets[0]
                form = MeetingSignInForm(
                                question_text=sign_in_sheet.quick_question
                )
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Sign into Meeting',
        'form_title': 'Sign into %s' % (event.name),
        'help_text': ('Please enter the meeting sign-in code and answer the '
                      'following quick survey questions'),
        'base': 'event_cal/base_event_cal.html',
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def event_detail(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if event.event_type.name == 'Conducted Interviews':
        return redirect('event_cal:interview_view_actives', event_id)
    elif event.event_type.name == 'Attended Interviews':
        return redirect('event_cal:interview_view_electees', event_id)

    request.session['current_page'] = request.path
    has_profile = False
    user_is_member = False
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        user_is_member = request.user.userprofile.is_member()
    template = loader.get_template('event_cal/detail.html')
    request.session['project_report_event'] = event_id
    context_dict = {
        'event': event,
        'has_profile': hasattr(request.user, 'userprofile'),
        'is_member': user_is_member,
        'can_edit_event': Permissions.can_edit_event(event, request.user),
        'can_add_sign_in': (Permissions.can_create_events(request.user) and not MeetingSignIn.objects.filter(event=event).exists() and event.use_sign_in),
        'can_complete': (event.can_complete_event() and Permissions.can_edit_event(event, request.user)),
        'can_edit_signin': (not event.can_complete_event() and
                            Permissions.can_edit_event(event, request.user) and
                            event.use_sign_in),
        'subnav': 'list',
        'show_shifts': True,
        'needs_social_media': True,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


@ajax
@login_required
def add_to_waitlist(request, shift_id):
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    if shift.start_time < timezone.now():
        request.session['error_message'] = 'You cannot sign up for an event in the past'
    elif not (shift.max_attendance and (shift.attendees.count() >= shift.max_attendance)):
        request.session['error_message'] = 'Shift isn\'t full'
    elif shift.max_attendance == 0:
        request.session['error_message'] = 'Shift has capacity 0, unable to add to waitlist'
    elif hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        existing_waitlist = WaitlistSlot.objects.filter(shift=shift, user=profile).exists()
        if existing_waitlist:
            request.session['error_message'] = 'You are already on the waitlist'
        elif (event.requires_AAPS_background_check and
              not BackgroundCheck.user_can_mindset(profile)):
            request.session['error_message'] = ('You must pass an AAPS '
                                                'background check and complete'
                                                ' training to sign up for this'
                                                'event')
        elif (event.requires_UM_background_check and
              not BackgroundCheck.user_can_work_w_minors(profile)):
            request.session['error_message'] = ('You must pass a UM background'
                                                ' check and complete training '
                                                'to sign up for this event')
        elif (event.mutually_exclusive_shifts and
              profile in event.get_event_attendees()):
            request.session['error_message'] = ('You may only sign up for one '
                                                'shift for this event. Unsign '
                                                'up for the other before '
                                                'continuing')
        elif profile.is_member or not event.members_only:
            if shift.ugrads_only and not profile.is_ugrad():
                request.session['error_message'] = 'Shift is for undergrads only'
            elif shift.grads_only and not profile.is_grad():
                request.session['error_message'] = 'Shift is for grads only'
            elif shift.electees_only and not profile.is_electee():
                request.session['error_message'] = 'Shift is for electees only'
            elif shift.actives_only and not profile.is_active():
                request.session['error_message'] = 'Shift is for actives only'
            elif not event.allow_overlapping_sign_ups and event.does_shift_overlap_with_users_other_shifts(shift, request.user.userprofile):
                request.session['error_message'] = 'You are signed up for a shift that overlaps with this one.'
            else:
                waitlist = WaitlistSlot(shift=shift, user=profile)
                waitlist.save()
                request.session['success_message'] = ('You have successfully '
                                                      'been added to the '
                                                      'waitlist.')
        else:
            request.session['error_message'] = 'This event is members-only'
    else:
        request.session['error_message'] = ('You must create a profile before '
                                            'signing up to events')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (
                        request.session.pop('error_message')
                )
            }
        }
    return {
        'fragments': {
            '#shift-waitlist'+shift_id: r'''<a id="shift-waitlist%s" class="btn btn-primary btn-sm" onclick="$('#shift-waitlist%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-waitlist%s').attr('disabled',false);})"><i class="glyphicon glyphicon-remove"></i> Leave waitlist (there are currently %s users ahead of you).</a>''' % (
                            shift_id,
                            shift_id,
                            reverse(
                                'event_cal:remove_from_waitlist',
                                args=[shift_id]
                            ),
                            shift_id,
                            shift.get_users_waitlist_spot(profile)
            ),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (
                            request.session.pop('success_message')
            )
        }
    }


@ajax
@login_required
def remove_from_waitlist(request,  shift_id):
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    if shift.start_time < timezone.now():
        request.session['error_message'] = 'You cannot unsign-up for an event that has started'
    else:
        if hasattr(request.user, 'userprofile'):
            existing_waitlist = WaitlistSlot.objects.filter(
                                    shift=shift,
                                    user=request.user.userprofile
            )
            existing_waitlist.delete()
            request.session['success_message'] = 'You have successfully unsigned up from the waitlist.'
        else:
            request.session['error_message'] = 'You must create a profile before unsigning up'
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (
                    request.session.pop('error_message')
                )
            }
        }
    return {
        'fragments': {
            '#shift-waitlist'+shift_id: r'''<a id="shift-waitlist%s" class="btn btn-primary btn-sm" onclick="$('#shift-waitlist%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-waitlist%s').attr('disabled',false);})"><i class="glyphicon glyphicon-ok"></i> Add self to waitlist (there
            are currently %s users ahead of you)</a>''' % (
                        shift_id,
                        shift_id,
                        reverse(
                            'event_cal:add_to_waitlist',
                            args=[shift_id]
                        ),
                        shift_id,
                        shift.get_waitlist_length()
            ),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (
                request.session.pop('success_message')
            )
        }
    }


@ajax
@login_required
def add_shift_to_gcal(request,  shift_id):
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        if profile not in shift.attendees.all():
            request.session['error_message'] = ('You can only add events you '
                                                'have signed up for to your '
                                                'google calendar')
        else:
            email_pref = UserPreference.objects.filter(
                                user=profile,
                                preference_type='google_calendar_account'
            )
            if email_pref.exists():
                cal_email_pref = email_pref[0].preference_value
            else:
                cal_email_pref = GCAL_ACCT_PREF['default']
            if (cal_email_pref == 'umich' or
               not profile.is_member() or
               not profile.memberprofile.alt_email):
                email_to_use = profile.uniqname+'@umich.edu'
            else:
                email_to_use = profile.memberprofile.alt_email
            shift.add_attendee_to_gcal(
                    profile.get_firstlast_name(),
                    email_to_use
            )
            request.session['success_message'] = ('You have successfully '
                                                  'added the event to '
                                                  'your gcal')
    else:
        request.session['error_message'] = ('You must create a profile before '
                                            'adding the event to your google '
                                            'calendar')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))
            }
        }
    return {
        'fragments': {
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s
    </div>''' % (request.session.pop('success_message'))
        }
    }


@ajax
@login_required
def add_shift_to_gcal_paired(request,  shift_id):
    shift = get_object_or_404(InterviewPairing, id=shift_id)
    event = shift.first_shift.event
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        if profile not in shift.first_shift.attendees.all():
            request.session['error_message'] = ('You can only add events you '
                                                'have signed up for to your '
                                                'google calendar')
        else:
            email_pref = UserPreference.objects.filter(
                                user=profile,
                                preference_type='google_calendar_account'
            )
            if email_pref.exists():
                cal_email_pref = email_pref[0].preference_value
            else:
                cal_email_pref = GCAL_ACCT_PREF['default']
            if (cal_email_pref == 'umich' or
               not profile.is_member() or
               not profile.memberprofile.alt_email):
                email_to_use = profile.uniqname+'@umich.edu'
            else:
                email_to_use = profile.memberprofile.alt_email
            shift.first_shift.add_attendee_to_gcal(
                                        profile.get_firstlast_name(),
                                        email_to_use
            )
            shift.second_shift.add_attendee_to_gcal(
                                        profile.get_firstlast_name(),
                                        email_to_use
            )
            request.session['success_message'] = ('You have successfully added'
                                                  ' the event to your gcal')
    else:
        request.session['error_message'] = ('You must create a profile before '
                                            'adding the event to your google '
                                            'calendar')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))
            }
        }
    return {
        'fragments': {
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s
    </div>''' % (request.session.pop('success_message'))
        }
    }


@ajax
@login_required
def sign_up(request,  shift_id):
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    if shift.start_time < timezone.now():
        request.session['error_message'] = ('You cannot sign up for an event '
                                            'in the past')
    elif shift.start_time-timedelta(hours=event.min_sign_up_notice) < timezone.now():
        request.session['error_message'] = 'This event blocks sign-up %s hours before start' % (event.min_sign_up_notice)
    elif shift.max_attendance and (shift.attendees.count() >= shift.max_attendance):
        request.session['error_message'] = 'Shift is full'
    else:
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if event.requires_AAPS_background_check and not BackgroundCheck.user_can_mindset(profile):
                request.session['error_message'] = 'You must pass an AAPS background check and complete training to sign up for this event'
            elif event.requires_UM_background_check and not BackgroundCheck.user_can_work_w_minors(profile):
                request.session['error_message'] = 'You must pass a UM background check and complete training to sign up for this event'
            elif event.mutually_exclusive_shifts and profile in event.get_event_attendees():
                request.session['error_message'] = 'You may only sign up for one shift for this event. Unsign up for the other before continuing'
            elif profile.is_member or not event.members_only:
                if shift.ugrads_only and not profile.is_ugrad():
                    request.session['error_message'] = 'Shift is for undergrads only'
                elif shift.grads_only and not profile.is_grad():
                    request.session['error_message'] = 'Shift is for grads only'
                elif shift.electees_only and not profile.is_electee():
                    request.session['error_message'] = 'Shift is for electees only'
                elif shift.actives_only and not profile.is_active():
                    request.session['error_message'] = 'Shift is for actives only'
                elif not event.allow_overlapping_sign_ups and event.does_shift_overlap_with_users_other_shifts(shift, request.user.userprofile):
                    request.session['error_message'] = 'You are signed up for a shift that overlaps with this one.'
                else:
                    add_user_to_shift(request.user.userprofile, shift)
                    request.session['success_message'] = 'You have successfully signed up for the event'
                    if event.preferred_items and event.preferred_items.lstrip() and not event.usercanbringpreferreditem_set.filter(user=profile).exists():
                        request.session['info_message'] = 'Please indicate if you can bring items to the event.'
                        return redirect('event_cal:preferred_items_request', shift.event.id)
                    elif event.needs_carpool and not event.carpoolperson_set.filter(person=profile).exists():
                        request.session['info_message'] = 'If you need or can give a ride, please also sign up for the carpool'
                        return redirect('event_cal:carpool_sign_up', shift.event.id)
            else:
                request.session['error_message'] = 'This event is members-only'
        else:
            request.session['error_message'] = ('You must create a profile '
                                                'before signing up to events')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s
    </div>''' % (request.session.pop('error_message'))
            }
        }
    return_dict = {
        'fragments': {
            '#shift-signup'+shift_id: r'''
            <a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-remove"></i> Unsign-up</a>
            ''' % (
                shift_id,
                shift_id,
                reverse(
                    'event_cal:unsign_up',
                    args=[shift_id]
                ),
                shift_id
            ),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s
    </div>''' % (request.session.pop('success_message'))
        }
    }
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        gcal_pref = UserPreference.objects.filter(
                            user=profile,
                            preference_type='google_calendar_add'
        )
        if gcal_pref.exists():
            use_cal_pref = gcal_pref[0].preference_value
        else:
            use_cal_pref = GCAL_USE_PREF['default']
        show_manual_add_gcal_button = (use_cal_pref != 'always')
    else:
        show_manual_add_gcal_button = False
    if show_manual_add_gcal_button:
        return_dict['fragments']['#shift-gcal'+shift_id] = r'''
        <a id="shift-gcal%s" class="btn btn-primary btn-sm" onclick="$('#shift-gcal%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-gcal%s').attr('disabled',false);})"><i class="glyphicon glyphicon-calendar"></i> Add event to gcal</a>
        ''' % (
            shift_id,
            shift_id,
            reverse(
                'event_cal:add_shift_to_gcal',
                args=[shift_id]
            ),
            shift_id
        )
    return return_dict


def unsign_up_user(shift, profile):
    remove_user_from_shift(profile, shift)
    waitlist = shift.get_ordered_waitlist()
    if waitlist.exists():
        w = waitlist[0]
        add_user_to_shift(w.user, shift)
        notify_waitlist_move(shift.event, shift, w.user)
        w.delete()
    if profile not in shift.event.get_event_attendees():
        CarpoolPerson.objects.filter(
                event=shift.event,
                person=profile
        ).delete()
        UserCanBringPreferredItem.objects.filter(
                event=shift.event,
                user=profile
        ).delete()


@ajax
@login_required
def manual_remove_user_from_shift(request, shift_id, username):
    shift = get_object_or_404(EventShift, id=shift_id)
    e = shift.event
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = 'You are not authorized to remove attendees'
    else:
        shift = get_object_or_404(EventShift, id=shift_id)
        profile = get_object_or_404(UserProfile, uniqname=username)
        unsign_up_user(shift, profile)
        request.session['success_message'] = 'You have successfully unsigned up %s from the event.' % (username)
    if 'error_message' in request.session:
        return {'fragments': {'#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))}}
    return_dict = {
        'fragments': {
            '#shift-'+shift_id+'-attendee-'+username: '',
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s
    </div>''' % (request.session.pop('success_message'))
        }
    }
    if username == request.user.username:
        return_dict['fragments']['#shift-signup'+shift_id] = r'''
        <a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-ok"></i> Sign-up</a>
        ''' % (
            shift_id,
            shift_id,
            reverse('event_cal:sign_up', args=[shift_id]),
            shift_id
        )
    return return_dict


@ajax
@login_required
def unsign_up(request, shift_id):
    shift = get_object_or_404(EventShift, id=shift_id)
    event = shift.event
    if shift.start_time < timezone.now():
        request.session['error_message'] = ('You cannot unsign-up for an '
                                            'event that has started')
    elif shift.start_time-timedelta(hours=event.min_unsign_up_notice) < timezone.now():
        request.session['error_message'] = 'This event blocks unsign-up %s hours before start' % (event.min_unsign_up_notice)
    else:
        if hasattr(request.user, 'userprofile'):
            unsign_up_user(shift, request.user.userprofile)

            request.session['success_message'] = ('You have successfully '
                                                  'unsigned up from the '
                                                  'event.')
        else:
            request.session['error_message'] = ('You must create a profile '
                                                'before unsigning up')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))
            }
        }

    return {
        'fragments': {
            '#shift-'+shift_id+'-attendee-'+request.user.username: '',
            '#shift-signup'+shift_id: r'''
    <a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-ok"></i> Sign-up</a>
    ''' % (
                shift_id,
                shift_id,
                reverse('event_cal:sign_up', args=[shift_id]),
                shift_id
            ),
            '#shift-gcal'+shift_id: r'''
    <a id="shift-gcal%s" class="hidden"></a>''' % (shift_id),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s
    </div>''' % (request.session.pop('success_message'))
        }
    }


@login_required
def carpool_sign_up(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if not hasattr(request.user, 'userprofile'):
        request.session['error_message'] = ('You must create  profile before '
                                            'signing up to a carpool')
        return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(event_id,)
        )
    profile = request.user.userprofile
    if not event.needs_carpool:
        request.session['error_message'] = ('A carpool isn\'t set up for '
                                            'this event.')
        return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(event_id,)
        )
    if event.carpoolperson_set.filter(person=profile).exists():
        request.session['warning_message'] = ('You are already signed up for '
                                              'the carpool.')
        return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(event_id,)
        )
    CarpoolForm = modelform_factory(
                        CarpoolPerson,
                        exclude=('person', 'event')
    )
    form = CarpoolForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            instance.person = profile
            instance.event = event
            instance.save()
            request.session['success_message'] = ('You have signed up for '
                                                  'the carpool')
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(event_id,)
            )
        else:
            request.session['warning_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Sign up for Carpool',
        'form_title': 'Sign up for carpool for  %s' % (event.name),
        'help_text': ('If you need a ride or can drive people, please sign up '
                      'to participate in the carpool'),
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


@login_required
def preferred_items_request(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if not hasattr(request.user, 'userprofile'):
        request.session['error_message'] = ('You must create  profile before '
                                            'indicating you can bring an item')
        return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(event_id,)
        )
    profile = request.user.userprofile
    if not event.preferred_items.lstrip():
        request.session['error_message'] = ('This event doesn\'t need any '
                                            'items.')
        return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(event_id,)
        )
    if event.usercanbringpreferreditem_set.filter(user=profile).exists():
        request.session['warning_message'] = ('You already indicated if you '
                                              'can bring the needed items.')
        return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(event_id,)
        )
    ItemForm = modelform_factory(
                    UserCanBringPreferredItem,
                    exclude=('user', 'event')
    )
    form = ItemForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = profile
            instance.event = event
            instance.save()
            request.session['success_message'] = ('You have indicated if you '
                                                  'can bring the item(s) '
                                                  'needed.')
            if event.needs_carpool:
                request.session['info_message'] = ('If you need or can give a '
                                                   'ride, please also sign up '
                                                   'for the carpool')
                return redirect('event_cal:carpool_sign_up', event_id)
            return get_previous_page(
                            request,
                            alternate='event_cal:event_detail',
                            args=(event_id,)
            )
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Submit',
        'form_title': 'Can you bring the needed/preferred items?',
        'help_text': ('This event needs the following items:\n' +
                      event.preferred_items +
                      '\nWhile it is not required that you bring them, it is '
                      'helpful. Please indicate if you can bring them.'),
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


@login_required
def add_event_photo(request):
    if (not hasattr(request.user, 'userprofile') and
       request.user.userprofile.is_member()):
        request.session['error_message'] = ('You must create  profile before '
                                            'adding photos')
        return get_previous_page(request, alternate='event_cal:index')
    if Permissions.can_create_events(request.user):
        EventPhotoForm = modelform_factory(
                            EventPhoto,
                            form=BaseEventPhotoForm
        )
        has_pr = True
    else:
        EventPhotoForm = modelform_factory(
                            EventPhoto,
                            form=BaseEventPhotoFormAlt
        )
        has_pr = False
    prs = Permissions.project_reports_you_can_view(request.user)
    events = CalendarEvent.get_current_term_events_alph()
    if request.method == 'POST':
        form = EventPhotoForm(request.POST, request.FILES)
        form.fields['event'].queryset = events
        if has_pr:
            form.fields['project_report'].queryset = prs
        if form.is_valid():
            form.save()
            request.session['success_message'] = 'Photo successfully submitted'
            return get_previous_page(request, alternate='event_cal:index')
        else:
            request.session['warning_message'] = messages.GENERIC_SUBMIT_ERROR
    else:
        form = EventPhotoForm()
        form.fields['event'].queryset = events
        if has_pr:
            form.fields['project_report'].queryset = prs
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'photo',
        'has_files': True,
        'submit_name': 'Add Event Photo',
        'form_title': 'Add Event Photo',
        'help_text': ('You may optionally associate the photo with a '
                      'particular event and/or project report.'),
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def list(request):
    request.session['current_page'] = request.path
    user_is_member = False
    has_profile = False
    query_members = Q(members_only=False)
    query_event_type = Q()
    query_location = Q()
    q_can_attend = Q()
    selected_boxes = []
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        if request.user.userprofile.is_member():
            user_is_member = True
            query_members = Q()
    if request.method == 'POST':
        form = EventFilterForm(request.POST)
        query_date = Q()
        if form.is_valid():
            after_date = form.cleaned_data['after_date']
            if after_date:
                after_datetime = timezone.make_aware(
                                    datetime.combine(
                                                after_date,
                                                datetime.min.time()
                                    ),
                                    timezone.get_default_timezone()
                )
                query_date = (query_date &
                              Q(end_time__gte=after_datetime))
            before_date = form.cleaned_data['before_date']
            if before_date:
                before_datetime = datetime.combine(
                                            before_date,
                                            datetime.max.time()
                )
                query_date = (query_date &
                              Q(start_time__lte=before_datetime))
            on_campus = form.cleaned_data['on_campus']
            if on_campus:
                query_location = Q(on_campus=True)
            can_attend = form.cleaned_data['can_attend']
            if can_attend and user_is_member:
                profile = request.user.userprofile
                q_can_attend = (Q(ugrads_only=profile.is_ugrad()) |
                                Q(ugrads_only=False))
                q_can_attend &= (Q(grads_only=profile.is_grad()) |
                                 Q(grads_only=False))
                q_can_attend &= (Q(actives_only=profile.is_active()) |
                                 Q(actives_only=False))
                q_can_attend &= (Q(electees_only=profile.is_electee()) |
                                 Q(electees_only=False))
            event_categories = form.cleaned_data['event_reqs']
            for category in event_categories:
                selected_boxes.append(category.id)
                query_event_type = category.get_children(query_event_type)
    else:
        now = timezone.localtime(timezone.now())
        starting_after_text = date.today().isoformat()
        query_date = Q(end_time__gte=now)
        if not Permissions.view_officer_meetings_by_default(request.user):
            query_event_type = ~Q(event_type__name='Officer Meetings')
        initial = {'after_date': starting_after_text}
        form = EventFilterForm(initial=initial)
    shifts = EventShift.objects.filter(query_date)
    shifts = shifts.filter(query_location & q_can_attend)
    events = CalendarEvent.objects.filter(
                    query_members
    ).distinct()
    events = events.filter(eventshift__in=shifts).distinct()
    events = events.filter(query_event_type)
    template = loader.get_template('event_cal/list.html')
    packed_events = []
    for event in events.order_by('earliest_start'):
        packed_events.append(
                {
                    'event': event,
                    'can_edit': Permissions.can_edit_event(event, request.user)
                }
        )
    context_dict = {
        'events': packed_events,
        'user_is_member': user_is_member,
        'has_profile': has_profile,
        'form': form,
        'dp_ids': ['dp_before', 'dp_after'],
        'sorted_event_categories': EventCategory.flatten_category_tree(),
        'selected_boxes': selected_boxes,
        'subnav': 'list',
        'needs_social_media': True,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


@ajax
def get_event_ajax(request, event_id):
    has_profile = False
    cache_name = 'EVENT_AJAX'+event_id
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        if request.user.userprofile.is_active:
            cache_name +='ACTIVE'
        elif request.user.userprofile.is_ugrad:
            cache_name +='UGRAD_ELECTEE'
        else:
            cache_name += 'GRAD_ELECTEE'

    event_html = cache.get(cache_name, None)
    if not event_html:
        event = get_object_or_404(CalendarEvent, id=event_id)
        can_edit = Permissions.can_edit_event(event, request.user)
        
        context_dict = {
            'event': event,
            'can_edit_event': can_edit,
            'has_profile': has_profile,
            'user': request.user,
            'show_shifts': not (
                            event.event_type.name == 'Attended Interviews' or
                            event.event_type.name == 'Conducted Interviews'
                        ),
            }
        context_dict.update(get_permissions(request.user))
        context_dict.update(get_common_context(request))
        event_html = loader.render_to_string(
                        'event_cal/event.html',
                        context_dict
        )
        if event.eventshift_set.exclude(max_attendance=None).exists():
            cache.set('EVENT_AJAX'+event_id, event_html, 60*10)
        else:
            cache.set('EVENT_AJAX'+event_id, event_html, 60*60*2)

    return {
        'fragments': {
            '#event'+event_id: event_html
        }
    }


def my_events(request):
    request.session['current_page'] = request.path
    my_events = []
    has_profile = False
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        is_attendee = Q(
            term=AcademicTerm.get_current_term(),
            eventshift__attendees__uniqname=request.user.userprofile.uniqname
        )
        is_leader = Q(
            term=AcademicTerm.get_current_term(),
            leaders__uniqname=request.user.userprofile.uniqname
        )
        query = is_attendee | is_leader
        my_events = CalendarEvent.objects.filter(query).distinct().order_by('earliest_start')

    template = loader.get_template('event_cal/my_events.html')
    packed_events = []
    for event in my_events:
        packed_events.append(
            {
                'event': event,
                'can_edit': Permissions.can_edit_event(
                                event,
                                request.user
                )
            }
        )
    context_dict = {
        'my_events': packed_events,
        'has_profile': has_profile,
        'subnav': 'my_events',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def create_multishift_event(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message'] = 'You are not authorized to create events'
        return get_previous_page(request, alternate='event_cal:list')
    request.session['current_page'] = request.path
    EventForm = modelform_factory(
                    CalendarEvent,
                    form=BaseEventForm,
                    exclude=(
                        'completed',
                        'google_event_id',
                        'project_report',
                        'use_sign_in'
                    )
    )
    EventForm.base_fields['assoc_officer'].queryset = OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    form = EventForm(request.POST or None, prefix='event')
    formset = MultiShiftFormset(request.POST or None, prefix='shift')
    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            event = form.save()
            if not event.event_class:
                    s = event.name.split()
                    if re.match(NUMBER_OR_NUMERAL, s[-1]):
                        s = s[0:-1]
                    n = ' '.join(s).title()
                    ec = EventClass.objects.filter(name=n)
                    if ec.exists():
                        ec = ec[0]
                    else:
                        ec = EventClass(name=n)
                        ec.save()
                    event.event_class = ec
                    event.save()
            for shift_form in formset:
                if not shift_form.is_valid():
                    continue
                cleaned_data = shift_form.cleaned_data
                shift_date = cleaned_data['date']
                shifts_start = cleaned_data['start_time']
                mid_time = datetime.combine(shift_date, shifts_start)
                end_time = datetime.combine(shift_date, shift_form.cleaned_data['end_time'])
                while mid_time < end_time:
                    start_time = mid_time
                    mid_time += timedelta(minutes=shift_form.cleaned_data['duration'])
                    event_shift = EventShift()
                    event_shift.start_time = timezone.make_aware(start_time, timezone.get_current_timezone())
                    event_shift.end_time = timezone.make_aware(mid_time, timezone.get_current_timezone())
                    event_shift.location = shift_form.cleaned_data['location']
                    event_shift.ugrads_only = shift_form.cleaned_data['ugrads_only']
                    event_shift.grads_only = shift_form.cleaned_data['grads_only']
                    event_shift.max_attendance = shift_form.cleaned_data['max_attendance']
                    event_shift.electees_only = shift_form.cleaned_data['electees_only']
                    event_shift.actives_only = shift_form.cleaned_data['actives_only']
                    event_shift.event = event
                    event_shift.save()
            request.session['success_message'] = 'Event created successfully'
            event.add_event_to_gcal()
            event.notify_publicity()
            event.save()
            tweet_option = form.cleaned_data.pop('tweet_option', 'N')
            if tweet_option == 'T':
                event.tweet_event(False)
            elif tweet_option == 'H':
                event.tweet_event(True)
            return redirect('event_cal:list')

        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    dp_ids = ['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-date' % (count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form': form,
        'edit': True,
        'formset': formset,
        'dp_ids': dp_ids,
        'dp_ids_dyn': ['date'],
        'prefix': 'shift',
        'subnav': 'admin',
        'submit_name': 'Create Event',
        'form_title': 'Multiple shift event creation',
        'help_text': ('Easily create shifts with multiple, regularly spaced '
                      'events. Simply specify the start and end time for each '
                      'block of time and the shift length. Do not use this '
                      'for electee interview creation, use the intended '
                      'form.'),
        'shift_title': 'Shift days and time windows',
        'shift_help_text': ('Shifts will be automatically created within the '
                            'window you specify, for the duration you give. '
                            'Note that if your duration does not line up '
                            'with the end time, you may go longer than you '
                            'planned.'),
        'back_button': {
                'link': reverse('event_cal:calendar_admin'),
                'text': 'To Calendar Admin'
        },
        'event_photos': EventPhoto.objects.all(),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def create_event(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message'] = 'You are not authorized to create events'
        return get_previous_page(request, alternate='event_cal:list')
    request.session['current_page'] = request.path
    EventForm = modelform_factory(
                    CalendarEvent,
                    form=BaseEventForm,
                    exclude=('completed', 'google_event_id', 'project_report'),
    )
    EventForm.base_fields['assoc_officer'].queryset = OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    form = EventForm(request.POST or None, prefix='event')
    formset = EventShiftFormset(
                    request.POST or None,
                    prefix='shift',
                    instance=CalendarEvent(),
    )
    if request.method == 'POST':
        if form.is_valid():
            event = form.save(commit=False)
            formset = EventShiftFormset(
                                request.POST,
                                prefix='shift',
                                instance=event
            )
            formset[0].empty_permitted = False
            if formset.is_valid():
                event.save()
                if not event.event_class:
                    s = event.name.split()
                    if re.match(NUMBER_OR_NUMERAL, s[-1]):
                        s = s[0:-1]
                    n = ' '.join(s).title()
                    ec = EventClass.objects.filter(name=n)
                    if ec.exists():
                        ec = ec[0]
                    else:
                        ec = EventClass(name=n)
                        ec.save()
                    event.event_class = ec
                    event.save()
                form.save_m2m()
                formset.save()
                request.session['success_message'] = 'Event created successfully'
                event.add_event_to_gcal()
                event.notify_publicity()
                event.save()
                tweet_option = form.cleaned_data.pop('tweet_option', 'N')
                if tweet_option == 'T':
                    event.tweet_event(False)
                elif tweet_option == 'H':
                    event.tweet_event(True)
                if event.use_sign_in:
                    request.session['info_message'] = 'Please create a sign-in for %s' % (unicode(event),)
                    event_id = int(event.id)
                    return redirect('event_cal:create_meeting_signin', event_id)
                else:
                    return redirect('event_cal:list')
            else:
                request.session['error_message'] = messages.SHIFT_ERRORS
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    dp_ids = ['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-start_time_0' % (count))
        dp_ids.append('id_shift-%d-end_time_0' % (count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form': form,
        'edit': True,
        'formset': formset,
        'dp_ids': dp_ids,
        'dp_ids_dyn': ['start_time_0', 'end_time_0'],
        'prefix': 'shift',
        'subnav': 'admin',
        'submit_name': 'Create Event',
        'form_title': 'Create New Event',
        'help_text': '',
        'shift_title': 'Event Shifts',
        'shift_help_text': '',
        'back_button': {
                    'link': reverse('event_cal:calendar_admin'),
                    'text': 'To Calendar Admin'
        },
        'event_photos': EventPhoto.objects.all(),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def create_meeting_signin(request, event_id):
    if not Permissions.can_create_events(request.user):
        request.session['error_message'] = ('You are not authorized to create '
                                            'meeting signins.')
        return get_previous_page(request, alternate='event_cal:list')
    e = get_object_or_404(CalendarEvent, id=event_id)
    if not e.use_sign_in:
        request.session['error_message'] = ('You can only create a meeting '
                                            'signin for a meeting.')
        return get_previous_page(request, alternate='event_cal:list')
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = ('You can only create a meeting '
                                            'signin for a meeting you are'
                                            'a leader of,')
        return get_previous_page(request, alternate='event_cal:list')
    MeetingSignInForm = modelform_factory(MeetingSignIn, exclude=('event',))
    existing_signin = MeetingSignIn.objects.filter(event=e)
    if existing_signin.exists():
        ex_sign = existing_signin[0]
    else:
        ex_sign = None
    form = MeetingSignInForm(request.POST or None, instance=ex_sign)
    if request.method == 'POST':
        if form.is_valid():
            signin = form.save(commit=False)
            signin.event = e
            signin.save()
            request.session['success_message'] = 'Event created successfully'
            return redirect('event_cal:list')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Create  Sign-in',
        'back_button': {
                'link': reverse('event_cal:event_detail', args=[event_id]),
                'text': 'To %s Page' % (e.name)
        },
        'form_title': 'Add/Edit Sign in for %s' % (e.name),
        'help_text': ('In order to use the sign-in feature, please create a '
                      'sign-in form. Note that the form will automatically '
                      'have an optional \"Free Response\" question in '
                      'addition to the quick question you provide.'),
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def delete_event(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    if Permissions.can_edit_event(e, request.user) and not e.completed:
        e.delete_gcal_event()
        e.delete()
        call_command('reset_upcoming_events')
        request.session['success_message'] = 'Event deleted successfully'
        return redirect('event_cal:list')
    else:
        request.session['error_message'] = ('You do not have sufficient '
                                            'permissions to delete this '
                                            'event, or it has already been '
                                            'completed.')
        return redirect('event_cal:index')


@ajax
def delete_shift(request, shift_id):
    s = get_object_or_404(EventShift, id=shift_id)
    e = s.event
    if Permissions.can_edit_event(e, request.user):
        if not e.completed and e.eventshift_set.all().count() > 1:
            s.delete_gcal_event_shift()
            s.delete()
            e.save()
            call_command('reset_upcoming_events')
            request.session['success_message'] = 'Event shift deleted successfully'
        else:
            request.session['error_message'] = ('Shifts can only be deleted '
                                                'for open events with more '
                                                'than one shift.')
    else:
        request.session['error_message'] = ('You do not have sufficient '
                                            'permissions to delete this '
                                            'shift.')

    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (
                                request.session.pop('error_message')
                            )
            }
        }
    return {
        'fragments': {
            '#eventshift'+shift_id: '',
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (
                            request.session.pop('success_message')
                        )
        }
    }


def email_participants(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    if (not Permissions.can_edit_event(e, request.user) or
       not hasattr(request.user, 'userprofile') or
       not request.user.userprofile.is_member()):
        request.session['error_message'] = ('You are not authorized to email '
                                            'this event\'s participants.')
        return get_previous_page(request, alternate='event_cal:list')
    form = EventEmailForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            e.email_participants(
                        subject,
                        body,
                        request.user.userprofile.memberprofile
            )
            request.session['success_message'] = ('Event participants emailed '
                                                  'successfully')
            return redirect('event_cal:event_detail', event_id)
        else:
            request.session['error_message'] = ('You need to include a '
                                                'subject and a body.')
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Email Participants',
        'form_title': 'Specify Subject/Body for Emailing Participants',
        'help_text': ('Use this form to email all current event participants. '
                      'Event leaders will be cc\'ed and you will be the '
                      'reply-to address.'),
        'base': 'event_cal/base_event_cal.html',
        'back_button': {
                    'link': reverse('event_cal:event_detail', args=[event_id]),
                    'text': 'To  %s Page' % (e.name)
        },
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def edit_event(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = ('You are not authorized to edit '
                                            'this event')
        return get_previous_page(request, alternate='event_cal:list')
    request.session['current_page'] = request.path
    active_officers = OfficerPosition.objects.filter(enabled=True)
    EventForm = modelform_factory(
                    CalendarEvent,
                    form=BaseEventForm,
                    exclude=('completed', 'google_event_id', 'project_report')
    )
    EventForm.base_fields['assoc_officer'].queryset = active_officers
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    needed_flyer = e.needs_flyer
    needed_facebook = e.needs_facebook_event
    needed_COE_event = e.needs_COE_event
    previous_cal = e.google_cal
    prefix_ev = 'event'
    prefix_shift = 'shift'
    form = EventForm(request.POST or None, prefix=prefix_ev, instance=e)
    formset = EventShiftEditFormset(
                        request.POST or None,
                        prefix=prefix_shift,
                        instance=e
    )
    if request.method == 'POST':
        if form.is_valid():
            event = form.save(commit=False)
            formset = EventShiftEditFormset(request.POST,
                                            prefix=prefix_shift,
                                            instance=event)
            formset[0].empty_permitted = False
            if formset.is_valid():
                event.save()
                if not event.event_class:
                    s = event.name.split()
                    if re.match(NUMBER_OR_NUMERAL, s[-1]):
                        s = s[0:-1]
                    n = ' '.join(s).title()
                    ec = EventClass.objects.filter(name=n)
                    if ec.exists():
                        ec = ec[0]
                    else:
                        ec = EventClass(name=n)
                        ec.save()
                    event.event_class = ec
                    event.save()
                form.save_m2m()
                shifts = formset.save()
                event.add_event_to_gcal(previous_cal=previous_cal)
                tweet_option = form.cleaned_data.pop('tweet_option', 'N')
                if tweet_option == 'T':
                    event.tweet_event(False)
                elif tweet_option == 'H':
                    event.tweet_event(True)
                event.notify_publicity(needed_flyer=needed_flyer,
                                       needed_facebook=needed_facebook,
                                       needed_coe_event=needed_COE_event,
                                       edited=True)
                request.session['success_message'] = ('Event updated '
                                                      'successfully')
                for shift in shifts:
                    waitlist = shift.get_ordered_waitlist()
                    for w in waitlist:
                        if shift.is_full():
                            break
                        add_user_to_shift(w.user, shift)
                        notify_waitlist_move(event, shift, w.user)
                        w.delete()
                return redirect('event_cal:event_detail', event_id)
            else:
                request.session['error_message'] = messages.SHIFT_ERRORS
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    dp_ids = ['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-start_time_0' % (count))
        dp_ids.append('id_shift-%d-end_time_0' % (count))
    template = loader.get_template('event_cal/detail.html')
    context_dict = {
        'form': form,
        'formset': formset,
        'edit': True,
        'event': e,
        'dp_ids': dp_ids,
        'dp_ids_dyn': ['start_time_0', 'end_time_0'],
        'prefix': prefix_shift,
        'subnav': 'list',
        'submit_name': 'Submit Changes',
        'shift_title': 'Edit Shifts',
        'shift_help_text': '',
        'event_photos': EventPhoto.objects.all(),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def update_completed_event(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = ('You are not authorized to '
                                            'edit this event')
        return get_previous_page(
                        request,
                        alternate='event_cal:event_detail',
                        args=(event_id,)
                )
    if e.can_complete_event():
        request.session['error_message'] = ('This event hasn\'t been '
                                            'completed yet. Do that first.')
        return get_previous_page(
                    request,
                    alternate='event_cal:event_detail',
                    args=(event_id,)
            )
    if e.is_fixed_progress():
        form_type = CompleteFixedProgressEventFormSet
        is_fixed = True
    else:
        form_type = CompleteEventFormSet
        is_fixed = False
    form_prefix = 'update_event'
    if request.method == 'POST':
        formset = form_type(
                    request.POST,
                    prefix='update_event',
                    queryset=ProgressItem.objects.filter(related_event=e)
        )
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            first_shift = e.eventshift_set.all()[0]
            duplicate_progress = set()
            instances_list = [item[0] for item in formset.changed_objects]
            for instance in instances:
                if not instance.member.is_member():
                    continue
                if instance not in instances_list:
                    # double check they don't already have progress?
                    if not e.eventshift_set.filter(
                            attendees=instance.member
                            ).exists():
                        first_shift.attendees.add(instance.member)
                        first_shift.save()
                    if ProgressItem.objects.filter(
                            related_event=e,
                            member=instance.member
                            ).exists():
                        duplicate_progress |= set([instance.member])
                        continue
                    instance.term = AcademicTerm.get_current_term()
                    instance.event_type = e.event_type
                    instance.date_completed = date.today()
                    instance.related_event = e
                    instance.name = e.name
                if is_fixed:
                    instance.amount_completed = 1
                instance.save()
            for instance in formset.deleted_objects:
                for shift in e.eventshift_set.filter(
                                attendees=instance.member
                        ):
                    shift.attendees.remove(instance.member)
                    shift.save()

            if duplicate_progress:
                request.session['warning_message'] = (
                                'The following members had progress listed '
                                'twice, with latter listings ignored: ' +
                                ','.join(
                                    [prof.uniqname for prof
                                     in duplicate_progress]
                                ) +
                                '. Go to update progress to check that the '
                                'amount of progress is correct')
            request.session['success_message'] = ('Event and progress updated '
                                                  'successfully')
            return redirect('event_cal:event_detail', event_id)
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    else:
        formset = form_type(
                    prefix='update_event',
                    queryset=ProgressItem.objects.filter(
                                related_event=e
                        ).order_by('member__last_name')
        )
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset': formset,
        'prefix': form_prefix,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Update Event',
        'back_button': {
                'link': reverse('event_cal:event_detail', args=[event_id]),
                'text': 'To  %s Page' % (e.name)
        },
        'form_title': 'Update Completion Report for  %s' % (e.name),
        'help_text': ('Note that this is *not* the project report. Use '
                      'this to update the progress of an event that has '
                      'already been completed. Those with progress are '
                      'listed below.'),
        'can_add_row': True,
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


# TODO: change it so that the form has an extra column that is whether
# or not they signed in
# include the attendees as options as well -- not sure what this means
def complete_event(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = messages.EVT_NO_EDIT
        return get_previous_page(
                    request,
                    alternate='event_cal:event_detail',
                    args=(event_id,)
            )
    if not e.can_complete_event():
        request.session['error_message'] = ('This event can\'t be '
                                            'completed yet.')
        return get_previous_page(
                    request,
                    alternate='event_cal:event_detail',
                    args=(event_id,)
            )
    if e.is_fixed_progress():
        form_type = CompleteFixedProgressEventFormSet
        is_fixed = True
    else:
        form_type = CompleteEventFormSet
        is_fixed = False
    form_prefix = 'complete_event'
    if request.method == 'POST':
        formset = form_type(
                    request.POST,
                    prefix=form_prefix,
                    queryset=ProgressItem.objects.none()
        )
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            first_shift = e.eventshift_set.all()[0]
            duplicate_progress = set()
            for instance in instances:
                if not instance.member.is_member():
                    continue
                # double check they don't already have progress?
                if not e.eventshift_set.filter(
                            attendees=instance.member
                        ).exists():
                    first_shift.attendees.add(instance.member)
                    first_shift.save()
                if ProgressItem.objects.filter(
                            related_event=e,
                            member=instance.member
                        ).exists():
                    duplicate_progress |= set([instance.member])
                    continue
                instance.term = AcademicTerm.get_current_term()
                instance.event_type = e.event_type
                instance.date_completed = date.today()
                instance.related_event = e
                instance.name = e.name
                if is_fixed:
                    instance.amount_completed = 1
                instance.save()
            confirmed_attendees = MemberProfile.objects.filter(
                                                progressitem__related_event=e
            )
            for shift in e.eventshift_set.all():
                shift.waitlistslot_set.all().delete()
                for attendee in shift.attendees.exclude(
                                    pk__in=confirmed_attendees
                                ):
                    if attendee.is_member():
                        shift.attendees.remove(attendee)
                shift.save()
            e.completed = True
            e.save()
            if duplicate_progress:
                request.session['warning_message'] = (
                                    'The following members had progress '
                                    'listed twice, with latter listings '
                                    'ignored: ' +
                                    ','.join(
                                        [prof.uniqname for prof
                                         in duplicate_progress]
                                        ) +
                                    '. Go to update progress to check that '
                                    'the amount of progress is correct')
            request.session['success_message'] = ('Event and progress '
                                                  'updated successfully')
            request.session['project_report_event'] = event_id
            return redirect('event_cal:event_project_report', event_id)
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    else:
        # create initial
        initial = []
        attendees = UserProfile.objects.filter(
                        event_attendee__event=e
        ).distinct()
        for attendee in attendees.order_by('last_name'):
            if not attendee.is_member():
                continue
            if ProgressItem.objects.filter(
                                related_event=e,
                                member=attendee.memberprofile
                    ).exists():
                continue
            if is_fixed:
                initial.append({'member': attendee.memberprofile})
            else:
                initial.append(
                        {
                            'member': attendee.memberprofile,
                            'amount_completed': round(
                                    e.get_attendee_hours_at_event(attendee),
                                    2
                            )
                        }
                )
        form_type.extra = len(initial)+1
        formset = form_type(
                    prefix=form_prefix,
                    queryset=ProgressItem.objects.none(),
                    initial=initial
        )
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset': formset,
        'prefix': form_prefix,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Complete Event',
        'back_button': {
                'link': reverse('event_cal:event_detail', args=[event_id]),
                'text': 'To  %s Page' % (e.name)
        },
        'form_title': 'Completion Report for %s' % (e.name),
        'help_text': ('Note that this is *not* the project report. Use this '
                      'to assign progress for those who attended the event. '
                      'The list of those who signed up for the event, as well '
                      'as the number of hours they signed up for, is included '
                      'below. Please make any changes necessary and then '
                      'click the complete event button. If the event uses a '
                      'sign-in feature, only those who signed up in advance '
                      'but did not sign in are included below. Those who '
                      'signed in have already had their progress assigned.'),
        'can_add_row': True,
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def generate_announcements(request):
    if not Permissions.can_generate_announcements(request.user):
        request.session['error_message'] = messages.ANNOUNCE_NO_PERMISSIONS_GEN
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    now = timezone.localtime(timezone.now())
    announcement_parts = AnnouncementBlurb.get_current_blurbs()
    template = loader.get_template('event_cal/announcements.html')
    context_dict = {
        'announcement_parts': announcement_parts,
        'subnav': 'admin',
        'announcement_events': CalendarEvent.get_upcoming_events(True),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def add_announcement(request):
    if not Permissions.can_add_announcements(request.user):
        request.session['error_message'] = messages.ANNOUNCE_NO_PERMISSIONS_ADD
        return get_previous_page(request, alternate='event_cal:index')
    AnnouncementForm = modelform_factory(
                            AnnouncementBlurb,
                            form=BaseAnnouncementForm
    )
    form = AnnouncementForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            request.session['success_message'] = ('Announcement(s) submitted '
                                                  'successfully')
            return get_previous_page(request, alternate='event_cal:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    dp_ids = ['id_start_date', 'id_end_date']
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'dp_ids': dp_ids,
        'subnav': 'admin',
        'has_files': False,
        'submit_name': 'Submit Announcement',
        'form_title': 'Add an Announcement Section',
        'help_text': ('Add an announcement to be included in the weekly email '
                      'summary. Do not submit announcements for events. Those '
                      'are automatically included using the information '
                      'provided in the event details.'),
        'base': 'event_cal/base_event_cal.html',
        'back_button': {
                'link': reverse('event_cal:calendar_admin'),
                'text': 'To Calendar Admin'
        },
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def gcal_test(request):
    if not request.user.is_superuser:
        raise PermissionDenied()
    c = get_credentials()
    if c is None or c.invalid:
        return initialize_gcal()
    else:
        request.session['warning_message'] = messages.GCAL_STILL_GOOD
        return get_previous_page(request, alternate='event_cal:index')


def oauth(request):
    code = request.GET.get('code', None)
    process_auth(code)
    return get_previous_page(request, alternate='event_cal:list')


def event_project_report(request, event_id):
    e = get_object_or_404(CalendarEvent, id=event_id)
    request.session['project_report_event'] = event_id
    request.session.pop('project_report_non_event', None)
    request.session.pop('project_report_id', None)
    return project_report(request)


def project_report_by_id(request, report_id):
    request.session.pop('project_report_event', None)
    request.session.pop('project_report_non_event', None)
    request.session['project_report_id'] = report_id
    return project_report(request)


def non_event_project_report(request, ne_id):
    request.session.pop('project_report_event', None)
    request.session.pop('project_report_id', None)
    request.session['project_report_non_event'] = ne_id
    return project_report(request)


def project_report(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message'] = messages.PROJ_REP_NO_PERMISSIONS
        return get_previous_page(request, alternate='event_cal:index')
    related_event = request.session.pop('project_report_event', None)
    related_non_event = request.session.pop('project_report_non_event', None)
    report_id = request.session.pop('project_report_id', None)
    if related_event:
        event = CalendarEvent.objects.get(id=related_event)
        event_name = event.name
        if event.project_report:
            event_name = event.project_report.name
        ProjectReportForm = modelform_factory(ProjectReport, exclude=('term',))
    elif related_non_event:
        non_event = NonEventProject.objects.get(id=related_non_event)
        event_name = non_event.name
        if non_event.project_report:
            event_name = non_event.project_report.name
        ProjectReportForm = modelform_factory(ProjectReport, exclude=('term',))
    elif report_id:
        report = get_object_or_404(ProjectReport, id=report_id)
        event_name = report.name
        ProjectReportForm = modelform_factory(ProjectReport, exclude=('term',))
    else:
        event_name = 'Unspecified Event'
        ProjectReportForm = modelform_factory(ProjectReport)

    if request.method == 'POST':
        if related_event and event.project_report:
            form = ProjectReportForm(
                            request.POST,
                            instance=event.project_report
            )
        elif related_non_event and non_event.project_report:
            form = ProjectReportForm(
                            request.POST,
                            instance=non_event.project_report
            )
        elif report_id:
            form = ProjectReportForm(request.POST, instance=report)
        else:
            form = ProjectReportForm(request.POST)

        if form.is_valid():
            if related_event:
                pr = form.save(commit=False)
                event = CalendarEvent.objects.get(id=related_event)
                pr.term = event.term
                pr.save()
                event.project_report = pr
                event.save()
            elif related_non_event:
                pr = form.save(commit=False)
                pr.term = non_event.term
                pr.save()
                non_event.project_report = pr
                non_event.save()
            elif report_id:
                pr = form.save()
            else:
                pr = form.save()
                request.session['warning_message'] = ('Project report not '
                                                      'attached to event; '
                                                      'please fix this.')
            request.session['success_message'] = ('Project report created '
                                                  'successfully')
            return redirect('event_cal:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    else:
        if related_event and event.project_report:
            form = ProjectReportForm(instance=event.project_report)
        elif related_non_event and non_event.project_report:
            form = ProjectReportForm(instance=non_event.project_report)
        elif report_id:
            form = ProjectReportForm(instance=report)
        else:
            form = ProjectReportForm()
    template = loader.get_template('generic_form.html')
    dp_ids = ['id_planning_start_date']
    context_dict = {
        'form': form,
        'dp_ids': dp_ids,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Create/update project report',
        'form_title': 'Create project report for %s' % (event_name),
        'help_text': ('These are reports sent to the national organization '
                      'to determine eligibility for certain chapter awards. '
                      'They are also used for transition material to help '
                      'future project leaders perform a similar event. Please '
                      'be descriptive in your responses.'),
        'base': 'event_cal/base_event_cal.html',
        }
    if related_event:
        request.session['project_report_event'] = related_event
    if related_non_event:
        request.session['project_report_non_event'] = related_non_event
    if report_id:
        request.session['project_report_id'] = report_id
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def submit_tutoring_form(request):
    is_member = False
    if hasattr(request.user, 'userprofile'):
        is_member = request.user.userprofile.is_member()

    if not is_member:
        request.session['error_message'] = messages.TUTOR_NOT_MEMBER
        return get_previous_page(request, alternate='event_cal:index')

    profile = request.user.userprofile.memberprofile
    TutoringForm = modelform_factory(
                    TutoringRecord,
                    exclude=('approved', 'tutor',)
    )
    tutoring_chair = OfficerPosition.objects.filter(
                    name='Campus Outreach Officer'
    )
    current_chair = Officer.objects.filter(
                    position__name='Campus Outreach Officer',
                    term=AcademicTerm.get_current_term()
    ).distinct()
    if current_chair.exists():
        current_tutoring_chair = current_chair[0].user
        tutoring_chair_name = current_tutoring_chair.get_firstlast_name()+'\n'
    else:
        tutoring_chair_name = ''
    if tutoring_chair.exists():
        tutoring_email = tutoring_chair[0].email
        tutoring_name = tutoring_chair[0].name
    else:
        tutoring_email = 'tbp.campusoutreach@umich.edu'
        tutoring_name = 'Campus Outreach Officer'
    if request.method == 'POST':
        form = TutoringForm(request.POST)
        if form.is_valid():
            tutoring_record = form.save(commit=False)
            tutoring_record.tutor = profile
            tutoring_record.approved = False
            tutoring_record.save()
            request.session['success_message'] = ('Tutoring Form submitted '
                                                  'successfully')
            # TODO move these to a more sensible location
            # and use kyle & my email script
            recipient = tutoring_record.student_uniqname
            tutor_name = tutoring_record.tutor.get_firstlast_name()
            recipient_email = recipient+"@umich.edu"
            number_hours_str = str(tutoring_record.number_hours)
            number_hours = (
                number_hours_str.rstrip('0').rstrip('.')
                if '.' in number_hours_str
                else number_hours_str
            )
            body = r'''Hello!

%(tutor)s logged that you were tutored for %(hours)s hours on %(date)s.
We'd like to know how it went. If you have any feedback for us we invite you to
fill out an (anonymous) feedback form: https://goo.gl/L1L9oW

If you have any other questions about tutoring, please feel free to email me
at %(email)s,

Regards,
%(chair_name)s%(position_name)s
%(email)s

Note: This is an automated email. Please do not reply to it as responses
are not checked.''' % {
                'tutor': tutor_name,
                'hours': number_hours,
                'date': unicode(tutoring_record.date_tutored),
                'email': tutoring_email,
                'chair_name': tutoring_chair_name,
                'position_name': tutoring_name,
            }
            tutor_email_body = r'''Hello %(tutor)s!

Thank you for logging that you tutored %(tutoree)s for %(hours)s hours on %(date)s.
We'd like to know how it went. If you have any feedback for us we invite you to
fill out a feedback form: www.tinyurl.com/TBP-tutoring-survey-tutor

If you have any other questions about tutoring, please feel free to email me
at %(email)s,

Regards,
%(chair_name)s%(position_name)s
%(email)s

Note: This is an automated email. Please do not reply to it as responses
are not checked.''' % {
                'tutor': tutor_name,
                'hours': number_hours,
                'date': unicode(tutoring_record.date_tutored),
                'email': tutoring_email,
                'chair_name': tutoring_chair_name,
                'position_name': tutoring_name,
                'tutoree':recipient,
            }
            send_mail(
                'We want your feedback on your recent tutoring session.',
                body,
                tutoring_email,
                [recipient_email],
                fail_silently=True
            )
            send_mail(
                'We want your feedback on your recent tutoring session.',
                tutor_email_body,
                tutoring_email,
                [profile.get_email()],
                fail_silently=True
            )
            return get_previous_page(request, alternate='event_cal:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    else:
        form = TutoringForm()
    dp_ids = ['id_date_tutored']
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'dp_ids': dp_ids,
        'subnav': 'tutoring_form',
        'has_files': False,
        'submit_name': 'Submit Tutoring Form',
        'form_title': 'Tutoring Summary Form',
        'help_text': ('Please log your tutoring here. By submitting this form,'
                      ' you attest that you tutored the student for the '
                      'claimed number of hours. Note that the student will be '
                      'emailed and given the opportunity to provide anonymous '
                      'feedback.'),
        'base': 'event_cal/base_event_cal.html',
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def add_project_report_to_event(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if not (Permissions.can_edit_event(event, request.user) or
            Permissions.can_process_project_reports(request.user)):
        request.session['error_message'] = messages.EVT_NO_PERMISSIONS
        return get_previous_page(request, alternate='event_cal:index')
    initial = {'report': event.project_report}
    form = AddProjectReportForm(request.POST or None, initial=initial)
    reports = Permissions.project_reports_you_can_view(request.user)
    form.fields['report'].queryset = reports
    if request.method == 'POST':
        if form.is_valid():
            report = form.cleaned_data.pop('report', None)
            if report:
                event.project_report = report
                event.save()
            request.session['success_message'] = ('Project Report attached '
                                                  'successfully.')
            return get_previous_page(request, alternate='event_cal:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'list',
        'has_files': False,
        'submit_name': 'Add/Update Attached Report',
        'form_title': 'Attach project report to %s' % (event.name),
        'help_text': ('You may have several events that share a common '
                      'project report. Use this form to attach an existing '
                      'project report to this event.'),
        'base': 'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def calendar_admin(request):
    if not Permissions.can_view_calendar_admin(request.user):
        request.session['error_message'] = messages.CAL_ADMIN_NO_PERMISSIONS
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    template = loader.get_template('event_cal/calendar_admin.html')
    links = []
    if Permissions.can_create_events(request.user):
        links.append(
                {
                    'link': reverse('event_cal:create_event'),
                    'name': 'Add Event',
                }
        )
        links.append(
                {
                    'link': reverse('event_cal:create_multishift_event'),
                    'name': 'Add Event with many shifts',
                }
        )
    if Permissions.can_add_announcements(request.user):
        links.append(
                {
                    'link': reverse('event_cal:add_announcement'),
                    'name': 'Add Announcement'
                }
        )
    if Permissions.can_generate_announcements(request.user):
        links.append(
                {
                    'link': reverse('event_cal:generate_announcements'),
                    'name': 'Generate Announcements',
                }
        )
        links.append(
                {
                    'link': reverse('event_cal:edit_announcements'),
                    'name': 'Edit Announcements'
                }
        )
    if Permissions.can_add_event_photo(request.user):
        links.append(
                {
                    'link': reverse('event_cal:add_event_photo'),
                    'name': 'Add Event Photo'
                }
        )
    if Permissions.can_manage_electee_progress(request.user):
        links.append(
                {
                    'link': reverse('event_cal:create_electee_interviews'),
                    'name': 'Schedule Electee Interview Slots',
                }
        )
    context_dict = {
        'subnav': 'admin',
        'page_title': 'Calendar Administrative Functions',
        'links': links,
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def edit_announcements(request):
    if not Permissions.can_generate_announcements(request.user):
        request.session['error_message'] = messages.ANNOUNCE_NO_PERMISSIONS
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    now = timezone.localtime(timezone.now())
    announcement_parts = AnnouncementBlurb.objects.filter(
                                                end_date__gt=now.date()
    )
    AnnouncementFormSet = modelformset_factory(AnnouncementBlurb, exclude=[])
    prefix = 'announcements'
    formset = AnnouncementFormSet(
                request.POST or None,
                prefix=prefix,
                queryset=announcement_parts
    )
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = ('The announcements were '
                                                  'successfully updated.')
            return redirect('event_cal:calendar_admin')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR

    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset': formset,
        'subnav': 'admin',
        'has_files': False,
        'can_add_row': True,
        'submit_name': 'Update Announcements',
        'form_title': 'Edit Submitted Announcements',
        'help_text': ('Edit announcements for the current/future '
                      'announcement cycles.'),
        'base': 'event_cal/base_event_cal.html',
        'back_button': {
                'link': reverse('event_cal:calendar_admin'),
                'text': 'To Calendar Admin'
        },
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def event_detail_table(request, event_id):
    has_profile = False
    if hasattr(request.user, 'userprofile'):
        has_profile = True
    if not has_profile:
        request.session['error_message'] = messages.EVT_TABLE_REQS_PROFILE
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    template = loader.get_template('event_cal/table_view.html')
    event = get_object_or_404(CalendarEvent, id=event_id)
    shifts = event.eventshift_set.order_by('start_time')
    times = sorted(
                set(
                    [timezone.localtime(shift.start_time).time()
                     for shift in shifts]
                )
    )
    dates = sorted(
                set(
                    [timezone.localtime(shift.start_time).date()
                     for shift in shifts]
                )
    )
    organized_shifts = [
                {
                    'time': time,
                    'dates': [None for date in dates]
                } for time in times
    ]
    for time_count, time in enumerate(times):
        for date_count, date in enumerate(dates):
            shift = shifts.filter(
                        start_time=timezone.make_aware(
                                        datetime.combine(date, time),
                                        timezone.get_default_timezone()
                        )
            )
            if shift:
                organized_shifts[time_count]['dates'][date_count] = shift[0]
    context_dict = {
        'event': event,
        'can_edit_event': Permissions.can_edit_event(event, request.user),
        'shifts': organized_shifts,
        'dates': dates,
        'has_profile': True,
        'subnav': 'list',
        'needs_social_media': True,
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def create_electee_interviews(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message'] = messages.INTERVIEW_CANNOT_CREATE
        return get_previous_page(request, alternate='event_cal:list')
    request.session['current_page'] = request.path
    EventForm = modelform_factory(
                        CalendarEvent,
                        form=BaseEventForm,
                        exclude=(
                            'event_class',
                            'completed',
                            'google_event_id',
                            'project_report',
                            'event_type',
                            'members_only',
                            'needs_carpool',
                            'use_sign_in',
                            'allow_advance_sign_up',
                            'needs_facebook_event',
                            'needs_flyer',
                            'mutually_exclusive_shifts'
                        )
    )
    active_officers = OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].queryset = active_officers
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    active_type = EventCategory.objects.get(name='Conducted Interviews')
    electee_type = EventCategory.objects.get(name='Attended Interviews')
    if request.method == 'POST':
        form = EventForm(request.POST, prefix='event')
        formset = InterviewShiftFormset(request.POST, prefix='shift')
        if form.is_valid() and formset.is_valid():
            active_event = form.save(commit=False)
            active_event.event_type = active_type
            active_event.save()
            active_id = active_event.id
            form.save_m2m()
            leaders = active_event.leaders.all()
            electee_event = active_event
            electee_event.pk = None
            electee_event.save()
            active_event = CalendarEvent.objects.get(id=active_id)
            electee_event.event_type = electee_type
            electee_event.mutually_exclusive_shifts = True
            electee_event.leaders = leaders
            electee_event.name += ' (Electees)'
            active_event.name += ' (Actives)'
            active_event.save()
            electee_event.save()
            n = 'Electee Interviews'
            ec = EventClass.objects.filter(name=n)
            if ec.exists():
                ec = ec[0]
            else:
                ec = EventClass(name=n)
                ec.save()
            active_event.event_class = ec
            active_event.save()
            electee_event.event_class = ec
            electee_event.save()
            for shift_form in formset:
                if not shift_form.is_valid() or not shift_form.has_changed():
                    # if it hasn't changed, then it's an extra blank form
                    continue
                cleaned_data = shift_form.cleaned_data
                shift_date = cleaned_data['date']
                shifts_start = cleaned_data['start_time']
                mid_time = datetime.combine(shift_date, shifts_start)
                end_time = datetime.combine(
                                shift_date,
                                shift_form.cleaned_data['end_time']
                )
                locations = shift_form.cleaned_data['locations'].split(',')
                num_parts = shift_form.cleaned_data['number_of_parts']
                odd_shift = False
                alternate_last = (len(locations) % num_parts) == 1

                while mid_time < end_time:
                    odd_shift = not odd_shift
                    if num_parts > 1:
                        if odd_shift:
                            start_shifts = []
                        else:
                            end_shifts = []
                    start_time = mid_time
                    mid_time += timedelta(
                                    minutes=shift_form.cleaned_data['duration']
                    )
                    for idx, location in enumerate(locations):
                        if idx == (len(locations)-1) and alternate_last:
                            part = 1 if odd_shift else 2
                        else:
                            part = (idx % num_parts)+1
                        electee_shift = EventShift()
                        tz = timezone.get_current_timezone()
                        electee_shift.start_time = timezone.make_aware(
                                                            start_time,
                                                            tz
                        )
                        electee_shift.end_time = timezone.make_aware(
                                                            mid_time,
                                                            tz
                        )
                        if num_parts > 1:
                            electee_shift.location = location.lstrip() + ' (Part '+unicode(part)+')'
                        else:
                            electee_shift.location = location.lstrip()
                        interview_type = shift_form.cleaned_data['interview_type']
                        if interview_type == 'U' or interview_type == 'UI':
                            electee_shift.ugrads_only = True
                        elif interview_type == 'G' or interview_type == 'GI':
                            electee_shift.grads_only = True
                        electee_shift.max_attendance = 1
                        electee_shift.electees_only = True
                        electee_shift.event = electee_event
                        electee_shift.save()
                        electee_shift_id = electee_shift.id
                        active_shift = electee_shift
                        active_shift.pk = None
                        active_shift.save()
                        active_shift.max_attendance = 2
                        active_shift.electees_only = False
                        active_shift.actives_only = True
                        active_shift.event = active_event
                        if interview_type == 'U':
                            active_shift.ugrads_only = True
                            active_shift.grads_only = False
                        elif interview_type == 'G':
                            active_shift.grads_only = True
                            active_shift.ugrads_only = False
                        else:
                            active_shift.grads_only = False
                            active_shift.ugrads_only = False
                        active_shift.save()
                        interview_shift = InterviewShift()
                        interview_shift.interviewer_shift = active_shift
                        electee_shift = EventShift.objects.get(
                                                    id=electee_shift_id
                        )
                        interview_shift.interviewee_shift = electee_shift
                        interview_shift.term = active_event.term
                        interview_shift.save()
                        if num_parts > 1:
                            if odd_shift:
                                start_shifts.append(electee_shift)
                            else:
                                end_shifts.append(electee_shift)
                    if num_parts > 1 and not odd_shift:
                        for idx, start_shift in enumerate(start_shifts):
                            pairing = InterviewPairing(
                                        first_shift=start_shift,
                                        second_shift=end_shifts[idx-1]
                            )
                            pairing.save()

            request.session['success_message'] = 'Event created successfully'
            active_event.add_event_to_gcal()
            electee_event.add_event_to_gcal()
            active_event.save()
            electee_event.save()
            tweet_option = form.cleaned_data.pop('tweet_option', 'N')
            if tweet_option == 'T':
                event.tweet_event(False)
            elif tweet_option == 'H':
                event.tweet_event(True)
            return redirect('event_cal:list')
        else:
            request.session['error_message'] = messages.EVT_SUBMIT_ERROR
    else:
        form = EventForm(prefix='event')
        formset = InterviewShiftFormset(prefix='shift')
    dp_ids = ['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-date' % (count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form': form,
        'formset': formset,
        'dp_ids': dp_ids,
        'dp_ids_dyn': ['date'],
        'prefix': 'shift',
        'subnav': 'admin',
        'submit_name': 'Create Interview Slots',
        'form_title': 'Electee Interview Slot Creation',
        'help_text': ('Create the interview slots. Just one per session, '
                      'separate events will be automatically created for '
                      'actives and electees.\n Note: the \"Grad interviewee '
                      'anyone interviewer\" option is discouraged due to the '
                      'nature of the case studies.'),
        'shift_title': 'Shift days and time windows',
        'shift_help_text': ('Shifts will be automatically created within the '
                            'window you specify, for the duration you give. '
                            'Note that if your duration does not line up with '
                            'the end time, you may go longer than you '
                            'planned.'),
        'back_button': {
            'link': reverse('event_cal:calendar_admin'),
            'text': 'To Calendar Admin',
        },
        'event_photos': EventPhoto.objects.all(),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit'] = True
    return HttpResponse(template.render(context_dict, request))


def interview_view_electees(request, event_id):
    has_profile = False
    user_is_member = False
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        user_is_member = request.user.userprofile.is_member()
    if not user_is_member:
        request.session['error_message'] = messages.INTERVIEW_NOT_MEMBER
        return get_previous_page(request, alternate='event_cal:index')

    template = loader.get_template('event_cal/interview_view.html')
    event = get_object_or_404(CalendarEvent, id=event_id)
    if not event.event_type.name == 'Attended Interviews':
        request.session['error_message'] = messages.NOT_INTERVIEW
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    shifts = event.eventshift_set.order_by('start_time')
    is_two_part = False
    if shifts[0].pairing_first.exists() or shifts[0].pairing_second.exists():
        is_two_part = True
        shifts = InterviewPairing.objects.filter(
            first_shift__event=event
        ).distinct().order_by('first_shift__start_time')
    organized_shifts, locations = organize_shifts_interview(shifts, is_two_part)

    context_dict = {
        'event': event,
        'can_edit_event': Permissions.can_edit_event(event, request.user),
        'shifts': organized_shifts,
        'locations': locations,
        'has_profile': hasattr(request.user, 'userprofile'),
        'subnav': 'list',
        'is_two_part': is_two_part,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


def interview_view_actives(request, event_id):
    has_profile = False
    user_is_member = False
    user_is_active = False
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        user_is_member = request.user.userprofile.is_member()
        user_is_active = request.user.userprofile.is_active()
    if not user_is_member:
        request.session['error_message'] = messages.INTERVIEW_NOT_MEMBER
        return get_previous_page(request, alternate='event_cal:index')
    if not user_is_active:
        request.session['error_message'] = messages.INTERVIEW_NOT_ACTIVE
        return get_previous_page(request, alternate='event_cal:index')

    template = loader.get_template('event_cal/interview_view_actives.html')
    event = get_object_or_404(CalendarEvent, id=event_id)
    if not event.event_type.name == 'Conducted Interviews':
        request.session['error_message'] = messages.NOT_INTERVIEW
        return get_previous_page(request, alternate='event_cal:index')
    request.session['current_page'] = request.path
    request.session['current_page'] = request.path
    shifts = event.eventshift_set.order_by('start_time')

    organized_shifts, locations = organize_shifts_interview(shifts, False)
    context_dict = {
        'event': event,
        'can_edit_event': Permissions.can_edit_event(event, request.user),
        'shifts': organized_shifts,
        'locations': locations,
        'has_profile': has_profile,
        'subnav': 'list',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    return HttpResponse(template.render(context_dict, request))


# These are for the interview slots
@ajax
@login_required
def sign_up_paired(request, shift_id):
    shift = get_object_or_404(InterviewPairing, id=shift_id)
    event = shift.first_shift.event
    has_error = False
    ERROR_MSG = ''
    min_signup = event.min_sign_up_notice
    start_time = shift.first_shift.start_time
    num_attendees = shift.first_shift.attendees.count()
    max_attendance = shift.first_shift.max_attendance
    if start_time < timezone.now():
        has_error = True
        ERROR_MSG = messages.EVT_IN_PAST
    elif (start_time-timedelta(hours=min_signup) < timezone.now()):
        has_error = True
        ERROR_MSG = messages.EVT_SIGNUP_CLOSED % (min_signup)
    elif (max_attendance and
          (num_attendees >= max_attendance)):
        has_error = True
        ERROR_MSG = messages.SHIFT_FULL
    else:
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if (event.requires_AAPS_background_check and
               not BackgroundCheck.user_can_mindset(profile)):
                has_error = True
                ERROR_MSG = messages.EVT_NEEDS_AAPS_BACKGROUND
            elif (event.requires_UM_background_check and
                  not BackgroundCheck.user_can_work_w_minors(profile)):
                has_error = True
                ERROR_MSG = EVT_NEEDS_UM_BACKGROUND
            elif (event.mutually_exclusive_shifts and
                  profile in event.get_event_attendees()):
                has_error = True
                ERROR_MSG = EVT_ALLOWS_ONE_SHIFT
            elif profile.is_member or not event.members_only:
                if shift.first_shift.ugrads_only and not profile.is_ugrad():
                    has_error = True
                    ERROR_MSG = SHIFT_UGRADS_ONLY
                elif shift.first_shift.grads_only and not profile.is_grad():
                    has_error = True
                    ERROR_MSG = messages.SHIFT_GRADS_ONLY
                elif (shift.first_shift.electees_only and
                      not profile.is_electee()):
                    has_error = True
                    ERROR_MSG = SHIFT_ELECTEES_ONLY
                elif (shift.first_shift.actives_only and
                      not profile.is_active()):
                    has_error = True
                    ERROR_MSG = SHIFT_ACTIVES_ONLY
                else:
                    add_user_to_shift(
                                request.user.userprofile,
                                shift.first_shift
                    )
                    add_user_to_shift(
                                request.user.userprofile,
                                shift.second_shift
                    )
                    request.session['success_message'] = EVT_SIGNUP_SUCCESS
                    can_bring = event.usercanbringpreferreditem_set.filter(
                                                                user=profile
                    )
                    if (event.preferred_items.lstrip() and
                       not can_bring.exists()):
                        request.session['info_message'] = messages.ITEMS
                        return redirect(
                                'event_cal:preferred_items_request',
                                shift.event.id,
                        )
                    if event.needs_carpool:
                        request.session['info_message'] = messages.CARPOOL
                        return redirect('event_cal:carpool_sign_up', event_id)
            else:
                has_error = True
                ERROR_MSG = 'This event is members-only'
        else:
            has_error = True
            ERROR_MSG = 'You must create a profile before signing up to events'
    if has_error:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (ERROR_MSG)
            }
        }
    shift_id = unicode(shift.first_shift.id)
    return_dict = {
        'fragments': {
            '#shift-signup'+shift_id: r'''<a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-remove"></i> Unsign-up</a>''' % (shift_id, shift_id, reverse('event_cal:unsign_up_paired', args=[shift.id]), shift_id),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (request.session.pop('success_message'))
        }
    }
    if hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        gcal_pref = UserPreference.objects.filter(
                            user=profile,
                            preference_type='google_calendar_add'
        )
        if gcal_pref.exists():
            use_cal_pref = gcal_pref[0].preference_value
        else:
            use_cal_pref = GCAL_USE_PREF['default']
        show_manual_add_gcal_button = (use_cal_pref != 'always')
    else:
        show_manual_add_gcal_button = False
    if show_manual_add_gcal_button:
        return_dict['fragments']['#shift-gcal'+shift_id] = r'''<a id="shift-gcal%s" class="btn btn-primary btn-sm" onclick="$('#shift-gcal%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-gcal%s').attr('disabled',false);})"><i class="glyphicon glyphicon-calendar"></i> Add event to gcal</a>''' % (shift_id, shift_id, reverse('event_cal:add_shift_to_gcal_paired', args=[shift.id]), shift_id)
    return return_dict


@ajax
@login_required
def manual_remove_user_from_paired_shift(request, shift_id, username):
    shift = get_object_or_404(InterviewPairing, id=shift_id)
    e = shift.first_shift.event
    if not Permissions.can_edit_event(e, request.user):
        request.session['error_message'] = ('You are not authorized to remove '
                                            'attendees')
    else:
        profile = get_object_or_404(UserProfile, uniqname=username)
        unsign_up_user(shift.first_shift, profile)
        unsign_up_user(shift.second_shift, profile)

        request.session['success_message'] = ('You have successfully unsigned '
                                              'up %s from'
                                              ' the event.') % (username)
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))
            }
        }
    shift_id = unicode(shift.first_shift.id)
    return_dict = {
        'fragments': {
            '#shift-'+shift_id+'-attendee-'+username: '',
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (request.session.pop('success_message'))
        }
    }
    if username == request.user.username:
        return_dict['fragments']['#shift-signup'+shift_id] = r'''<a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-ok"></i> Sign-up</a>''' % (shift_id, shift_id, reverse('event_cal:sign_up_paired', args=[shift.id]), shift_id)
    return return_dict


@ajax
@login_required
def unsign_up_paired(request, shift_id):
    shift = get_object_or_404(InterviewPairing, id=shift_id)
    event = shift.first_shift.event
    start_time = shift.first_shift.start_time
    min_signup = event.min_unsign_up_notice
    if shift.first_shift.start_time < timezone.now():
        request.session['error_message'] = ('You cannot unsign-up for an event'
                                            ' that has started')
    elif start_time-timedelta(hours=min_signup) < timezone.now():
        request.session['error_message'] = messages.EVT_SIGNUP_CLOSED % (
                                                                min_signup
        )
    else:
        if hasattr(request.user, 'userprofile'):
            unsign_up_user(shift.first_shift, request.user.userprofile)
            unsign_up_user(shift.second_shift, request.user.userprofile)

            request.session['success_message'] = ('You have successfully '
                                                  'unsigned up from the '
                                                  'event.')
        else:
            request.session['error_message'] = ('You must create a profile '
                                                'before unsigning up')
    if 'error_message' in request.session:
        return {
            'fragments': {
                '#ajax-message': r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>''' % (request.session.pop('error_message'))
            }
        }
    shift_id = unicode(shift.first_shift.id)
    return {
        'fragments': {
            '#shift-'+shift_id+'-attendee-'+request.user.username: '',
            '#shift-gcal'+shift_id: r'''<a id="shift-gcal%s" class="hidden"></a>''' % (shift_id),
            '#shift-signup'+shift_id: r'''<a id="shift-signup%s" class="btn btn-primary btn-sm" onclick="$('#shift-signup%s').attr('disabled',true);ajaxGet('%s',function(){$('#shift-signup%s').attr('disabled',false);})"><i class="glyphicon glyphicon-ok"></i> Sign-up</a>''' % (shift_id, shift_id, reverse('event_cal:sign_up_paired', args=[shift.id]), shift_id),
            '#ajax-message': r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>''' % (request.session.pop('success_message'))
        }
    }
