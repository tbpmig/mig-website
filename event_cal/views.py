# Create your views here.
from datetime import datetime,date,timedelta

from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django import forms
from django.forms.models import modelformset_factory,modelform_factory
from django.db.models import Min,Q

from event_cal.forms import BaseEventPhotoForm,BaseEventPhotoFormAlt, BaseAnnouncementForm,BaseEventForm,EventShiftFormset, EventShiftEditFormset,CompleteEventFormSet, MeetingSignInForm, CompleteFixedProgressEventFormSet,EventFilterForm,AddProjectReportForm,InterviewShiftFormset,MultiShiftFormset,EventEmailForm
from event_cal.models import GoogleCalendar,CalendarEvent, EventShift, MeetingSignIn, MeetingSignInUserData,AnnouncementBlurb,CarpoolPerson,EventPhoto,InterviewShift
from history.models import ProjectReport, Officer,NonEventProject
from mig_main.models import OfficerPosition,PREFERENCES,UserPreference,MemberProfile,UserProfile,AcademicTerm
from mig_main.utility import get_previous_page, Permissions, get_message_dict
from outreach.models import TutoringRecord
from requirements.models import ProgressItem, EventCategory

from event_cal.gcal_functions import initialize_gcal, process_auth,get_credentials

GCAL_USE_PREF = [d for d in PREFERENCES if d.get('name') == 'google_calendar_add'][0]
GCAL_ACCT_PREF = [d for d in PREFERENCES if d.get('name') == 'google_calendar_account'][0]


def get_permissions(user):
    return {
        'can_submit_tutoring_form':(hasattr(user,'userprofile') and user.userprofile.is_member()),
        'can_view_calendar_admin':Permissions.can_view_calendar_admin(user),
    }
def get_common_context(request):
    upcoming_html = cache.get('upcoming_events_html',None)
    if not upcoming_html:
        upcoming_html=loader.render_to_string('event_cal/upcoming_events.html',{'upcoming_events':CalendarEvent.get_upcoming_events(),'now':timezone.localtime(timezone.now())})
        cache.set('upcoming_events_html',upcoming_html)
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'now':timezone.localtime(timezone.now()),
        'upcoming_html':upcoming_html,
        'edit_page':False,
        'main_nav':'cal',
        })
    return context_dict

#VIEWS
def index(request):
    request.session['current_page']=request.path
    template = loader.get_template('event_cal/calendar.html')
    gcals = GoogleCalendar.objects.filter(~Q(name='Office Hours Calendar'))
    if not Permissions.view_officer_meetings_by_default(request.user):
        gcals = gcals.filter(~Q(name='Officer Calendar'))
    context_dict = {
        "google_cals":gcals,
        'office_hours_cal':GoogleCalendar.objects.filter(name='Office Hours Calendar'),
        'subnav':'gcal',
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict)
    return HttpResponse(template.render(context))

@login_required
def meeting_sign_in(request,event_id,shift_id):
    event = get_object_or_404(CalendarEvent,id=event_id)
    sign_in_sheets = MeetingSignIn.objects.filter(event=event)
    current_tz = timezone.get_current_timezone()
    now = timezone.localtime(timezone.now())
    if sign_in_sheets:
        sign_in_sheet = sign_in_sheets[0]
    else:
        sign_in_sheet = None
    request.session['event_signed_up']=int(event_id)
    shift = get_object_or_404(EventShift,id=shift_id)
    if not shift.can_sign_in():
        if not event.use_sign_in:
            request.session['error_message']='Sign-in not available for this event'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        elif shift.is_full():
            request.session['error_message']='You cannot sign-in; the event is full'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        else:
            request.session['error_message']='You can only sign-in during the event'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))

            
    if not hasattr(request.user,'userprofile'):
        request.session['error_message']='You must create a profile before signing in to a meeting'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    elif not request.user.userprofile.is_member and event.members_only:
        request.session['error_message']='Sorry, this event is members-only'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    else:
        profile = request.user.userprofile
        if shift.ugrads_only and not profile.is_ugrad():
            request.session['error_message']='Shift is for undergrads only'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        elif shift.grads_only and not profile.is_grad():
            request.session['error_message']='Shift is for grads only'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        elif shift.electees_only and not profile.is_electee():
            request.session['error_message']='Shift is for electees only'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        elif shift.actives_only and not profile.is_active():
            request.session['error_message']='Shift is for actives only'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        if request.method =='POST':
            if not sign_in_sheet:
                form = MeetingSignInForm(request.POST)
            else:
                sign_in_sheet = sign_in_sheets[0]
                form = MeetingSignInForm(request.POST,question_text=sign_in_sheet.quick_question)
            if form.is_valid():
                if not sign_in_sheet or form.cleaned_data['secret_code']==sign_in_sheet.code_phrase:
                    if profile.is_member() and (profile.memberprofile not in event.get_attendees_with_progress()):
                        if sign_in_sheet:
                            user_data = MeetingSignInUserData()
                            user_data.meeting_data = sign_in_sheet
                            user_data.question_response = ''
                            if 'quick_question' in form.cleaned_data:
                                user_data.question_response = form.cleaned_data['quick_question']
                            user_data.free_response = ''
                            if 'free_response' in form.cleaned_data:
                                user_data.free_response = form.cleaned_data['free_response']
                                if not user_data.free_response:
                                    user_data.free_response='no response given'
                            user_data.save()
                        hours = (shift.end_time-shift.start_time).seconds/3600.0
                        if event.is_fixed_progress():
                            hours = 1
                        p=ProgressItem(member=profile.memberprofile,term=AcademicTerm.get_current_term(),amount_completed=hours,event_type=event.event_type,related_event=event,date_completed=date.today(),name=event.name)
                        p.save()
                        request.session['success_message']='You were signed in successfully'
                    elif profile.is_member():
                        request.session['warning_message']='You were already signed in'
                    shift.attendees.add(profile)
                    return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
                else:
                    request.session['error_message']='The meeting\'s secret code was wrong. You were not signed in.'
            else:
                request.session['error_message']='There were errors in your sign-in form; you were not signed in. Please correct the errors and try again.'
        else:
            if not sign_in_sheet:
                form = MeetingSignInForm()
            else:
                sign_in_sheet = sign_in_sheets[0]
                form = MeetingSignInForm(question_text=sign_in_sheet.quick_question)
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Sign into Meeting',
#        'back_button':{'link':reverse('member_resources:view_progress',args=[uniqname]),'text':'To %s\'s Progress'%(profile.get_firstlast_name())},
        'form_title':'Sign into %s'%(event.name),
        'help_text':'Please enter the meeting sign-in code and answer the following quick survey questions',
#        'can_add_row':False,
        'base':'event_cal/base_event_cal.html',
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict)
    return HttpResponse(template.render(context))

def event_detail(request,event_id):
    request.session['current_page']=request.path
    if 'event_signed_up' in request.session:
        event_signed_up = request.session['event_signed_up']
        del request.session['event_signed_up']
    else:
        event_signed_up = None
    has_profile =False
    user_is_member=False
    if hasattr(request.user,'userprofile'):  
        has_profile = True
        try:
            request.user.userprofile.memberprofile
            user_is_member = True
        except ObjectDoesNotExist:
            pass
    template = loader.get_template('event_cal/detail.html')
    event = get_object_or_404(CalendarEvent,id=event_id)
    request.session['project_report_event']=event_id
    context_dict = {
        'event':event,
        'has_profile':hasattr(request.user,'userprofile'),
        'event_signed_up':event_signed_up,
        'is_member':user_is_member,
        'can_edit_event':Permissions.can_edit_event(event,request.user),
        'can_add_sign_in':(Permissions.can_create_events(request.user) and not MeetingSignIn.objects.filter(event=event).exists() and event.use_sign_in),
        'can_complete':(event.can_complete_event() and Permissions.can_edit_event(event,request.user)),
        'subnav':'list',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

@login_required
def sign_up(request, event_id, shift_id):
    event = get_object_or_404(CalendarEvent,id=event_id)
    shift = get_object_or_404(EventShift,id=shift_id)
    request.session['event_signed_up']=int(event_id)
    if shift.start_time < timezone.now():
        request.session['error_message']='You cannot sign up for an event in the past'
    elif shift.max_attendance and (shift.attendees.count() >= shift.max_attendance):
        request.session['error_message']='Shift is full'
    else:
        if hasattr(request.user,'userprofile'):
            profile = request.user.userprofile
            if profile.is_member or not event.members_only:
                if shift.ugrads_only and not profile.is_ugrad():
                    request.session['error_message']='Shift is for undergrads only'
                elif shift.grads_only and not profile.is_grad():
                    request.session['error_message']='Shift is for grads only'
                elif shift.electees_only and not profile.is_electee():
                    request.session['error_message']='Shift is for electees only'
                elif shift.actives_only and not profile.is_active():
                    request.session['error_message']='Shift is for actives only'
                else:
                    shift.attendees.add(request.user.userprofile)
                    gcal_pref = UserPreference.objects.filter(user=request.user.userprofile,preference_type='google_calendar_add')
                    if gcal_pref.exists():
                        use_cal_pref = gcal_pref[0].preference_value
                    else:
                        use_cal_pref = GCAL_USE_PREF['default']
                    if use_cal_pref == 'always':
                        email_pref = UserPreference.objects.filter(user=request.user.userprofile,preference_type='google_calendar_account')
                        if email_pref.exists():
                            cal_email_pref = email_pref[0].preference_value
                        else:
                            cal_email_pref = GCAL_ACCT_PREF['default']
                        if cal_email_pref =='umich' or not request.user.userprofile.is_member() or not request.user.userprofile.memberprofile.alt_email:
                            email_to_use = request.user.userprofile.uniqname+'@umich.edu'
                        else:
                            email_to_use = request.user.userprofile.memberprofile.alt_email
                        shift.add_attendee_to_gcal(request.user.userprofile.get_firstlast_name(),email_to_use)

                    request.session['success_message']='You have successfully signed up for the event'
                    if event.needs_carpool:
                        request.session['info_message']='If you need or can give a ride, please also sign up for the carpool'
                        return redirect('event_cal:carpool_sign_up',event_id)
            else:
                request.session['error_message']='This event is members-only'
        else:
            request.session['error_message']='You must create a profile before signing up to events' 
    return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))

@login_required
def unsign_up(request, event_id, shift_id):
    event = get_object_or_404(CalendarEvent,id=event_id)
    shift = get_object_or_404(EventShift,id=shift_id)
    request.session['event_signed_up']=int(event_id)
    if shift.start_time < timezone.now():
        request.session['error_message']='You cannot unsign-up for an event that has started'
    else:
        if hasattr(request.user,'userprofile'):
            shift.attendees.remove(request.user.userprofile)
            email_pref = UserPreference.objects.filter(user=request.user.userprofile,preference_type='google_calendar_account')
            if email_pref.exists():
                cal_email_pref = email_pref[0].preference_value
            else:
                cal_email_pref = GCAL_ACCT_PREF['default']
            if cal_email_pref =='umich' or not request.user.userprofile.is_member() or not request.user.userprofile.memberprofile.alt_email:
                email_to_use = request.user.userprofile.uniqname+'@umich.edu'
            else:
                email_to_use = request.user.userprofile.memberprofile.alt_email
            shift.delete_gcal_attendee(email_to_use)
            CarpoolPerson.objects.filter(event=event,person=request.user.userprofile).delete()

            request.session['success_message']='You have successfully unsigned up from the event.'
        else:
            request.session['error_message']='You must create a profile before unsigning up'
    return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))

@login_required
def carpool_sign_up(request,event_id):
    event = get_object_or_404(CalendarEvent,id=event_id)
    if not hasattr(request.user,'userprofile'):
        request.session['error_message']='You must create  profile before signing up to a carpool'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    profile = request.user.userprofile
    if not event.needs_carpool:
        request.session['error_message']='A carpool isn\'t set up for this event.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if event.carpoolperson_set.filter(person=profile).exists():
        request.session['warning_message']='You are already signed up for the carpool.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    CarpoolForm = modelform_factory(CarpoolPerson,exclude=('person','event'))
    if request.method =='POST':
        form = CarpoolForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.person=profile
            instance.event=event
            instance.save()
            request.session['success_message']='You have signed up for the carpool'
            return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
        else:
            request.session['warning_message']='There were errors in your submission'
    else:
        form = CarpoolForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Sign up for Carpool',
        'form_title':'Sign up for carpool for  %s'%(event.name),
        'help_text':'If you need a ride or can drive people, please sign up to participate in the carpool',
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


@login_required
def add_event_photo(request):
    if not hasattr(request.user,'userprofile') and request.user.userprofile.is_member():
        request.session['error_message']='You must create  profile before adding photos'
        return get_previous_page(request,alternate='event_cal:index')
    if Permissions.can_create_events(request.user):# and not request.user.is_superuser:
        EventPhotoForm = modelform_factory(EventPhoto,form=BaseEventPhotoForm)
        has_pr=True
    else:
        EventPhotoForm = modelform_factory(EventPhoto,form=BaseEventPhotoFormAlt)
        has_pr=False
    if request.method =='POST':
        form = EventPhotoForm(request.POST,request.FILES)
        form.fields['event'].queryset = CalendarEvent.get_current_term_events_alph()
        if has_pr:
            form.fields['project_report'].queryset = Permissions.project_reports_you_can_view(request.user)
        if form.is_valid():
            form.save()
            request.session['success_message']='Photo successfully submitted'
            return get_previous_page(request,alternate='event_cal:index')
        else:
            request.session['warning_message']='There were errors in your submission'
    else:
        form = EventPhotoForm()
        form.fields['event'].queryset = CalendarEvent.get_current_term_events_alph()
        if has_pr:
            form.fields['project_report'].queryset = Permissions.project_reports_you_can_view(request.user)
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'photo',
        'has_files':True,
        'submit_name':'Add Event Photo',
        'form_title':'Add Event Photo',
        'help_text':'You may optionally associate the photo with a particular event and/or project report.',
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
        
def list(request):
    request.session['current_page']=request.path
    user_is_member = False
    has_profile = False
    event_signed_up = request.session.pop('event_signed_up',None)
    query_members = Q(members_only=False) 
    query_event_type=Q()
    query_location=Q()
    query_can_attend=Q()
    selected_boxes = []
    if hasattr(request.user,'userprofile'):  
        has_profile = True
        if request.user.userprofile.is_member():
            user_is_member = True
            query_members = Q()
    if request.method=='POST':
        form = EventFilterForm(request.POST)
        query_date=Q()
        if form.is_valid():
            after_date = form.cleaned_data['after_date']
            if after_date:
                after_datetime = datetime.combine(after_date,datetime.min.time())
                query_date=query_date & Q(eventshift__end_time__gte=after_datetime)
            before_date = form.cleaned_data['before_date']
            if before_date:
                before_datetime = datetime.combine(before_date,datetime.max.time())
                query_date=query_date & Q(eventshift__start_time__lte=before_datetime)
            on_campus = form.cleaned_data['on_campus']
            if on_campus:
                query_location=Q(eventshift__on_campus=True)
            can_attend = form.cleaned_data['can_attend']
            if can_attend and user_is_member:
                profile = request.user.userprofile
                query_can_attend=Q(eventshift__ugrads_only=profile.is_ugrad)|Q(eventshift__ugrads_only=False)
                query_can_attend&=Q(eventshift__grads_only=profile.is_grad)|Q(eventshift__grads_only=False)
                query_can_attend&=Q(eventshift__actives_only=profile.is_active)|Q(eventshift__actives_only=False)
                query_can_attend&=Q(eventshift__electees_only=profile.is_electee)|Q(eventshift__electees_only=False)
            event_categories = form.cleaned_data['event_reqs']
            for category in event_categories:
                selected_boxes.append(category.id)
                query_event_type=category.get_children(query_event_type)
    else:
        now = timezone.localtime(timezone.now())
        starting_after_text=date.today().isoformat()
        query_date=Q(eventshift__end_time__gte=now)  
        if not Permissions.view_officer_meetings_by_default(request.user):
            query_event_type = ~Q(event_type__name='Officer Meetings')
        initial={'after_date':starting_after_text}
        form = EventFilterForm(initial=initial)
    events = CalendarEvent.objects.filter(query_members&query_date&query_event_type&query_location&query_can_attend).distinct()
    template = loader.get_template('event_cal/list.html')
    packed_events=[]
    for event in events.annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift'):
        packed_events.append({'event':event,'can_edit':Permissions.can_edit_event(event,request.user)})
    context_dict = {
        'events':packed_events,
        'user_is_member':user_is_member,
        'has_profile':has_profile,
        'event_signed_up':event_signed_up,
        'form':form,
        'dp_ids':['dp_before','dp_after'],
        'sorted_event_categories':EventCategory.flatten_category_tree(),
        'selected_boxes':selected_boxes,
        'subnav':'list',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def my_events(request):
    request.session['current_page']=request.path
    event_signed_up=request.session.pop('event_signed_up',None)
    my_events = []
    events_im_leading = []
    has_profile = False
    if hasattr(request.user,'userprofile'):
        has_profile = True
        my_events = CalendarEvent.objects.filter(term=AcademicTerm.get_current_term(),eventshift__attendees__uniqname=request.user.userprofile.uniqname).distinct().annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift')

        events_im_leading = CalendarEvent.objects.filter(term=AcademicTerm.get_current_term(),leaders__uniqname=request.user.userprofile.uniqname).distinct().annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift')

    template = loader.get_template('event_cal/my_events.html')
    packed_events=[]
    for event in my_events:
        packed_events.append({'event':event,'can_edit':Permissions.can_edit_event(event,request.user)})
    context_dict = {
        'my_events':packed_events,
        'events_im_leading':events_im_leading,
        'has_profile':has_profile,
        'event_signed_up':event_signed_up,
        'subnav':'my_events',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def create_multishift_event(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create events'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,form=BaseEventForm,exclude=('completed','google_event_id','project_report','use_sign_in'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    if request.method == 'POST':
        form = EventForm(request.POST,prefix='event')
        formset = MultiShiftFormset(request.POST,prefix='shift')
        if form.is_valid() and formset.is_valid():
            event = form.save()

            for shift_form in formset:
                if not shift_form.is_valid():
                    continue
                cleaned_data=shift_form.cleaned_data
                shift_date=cleaned_data['date']
                shifts_start = cleaned_data['start_time']
                mid_time =datetime.combine(shift_date,shifts_start)
                end_time = datetime.combine(shift_date,shift_form.cleaned_data['end_time']) 
                while mid_time<end_time:
                    start_time = mid_time
                    mid_time +=timedelta(minutes=shift_form.cleaned_data['duration'])
                    event_shift = EventShift()
                    event_shift.start_time = timezone.make_aware(start_time,timezone.get_current_timezone())
                    event_shift.end_time = timezone.make_aware(mid_time,timezone.get_current_timezone())
                    event_shift.location = shift_form.cleaned_data['location']
                    event_shift.ugrads_only = shift_form.cleaned_data['ugrads_only']
                    event_shift.grads_only = shift_form.cleaned_data['grads_only']
                    event_shift.max_attendance = shift_form.cleaned_data['max_attendance']
                    event_shift.electees_only = shift_form.cleaned_data['electees_only']
                    event_shift.actives_only = shift_form.cleaned_data['actives_only']
                    event_shift.event = event    
                    event_shift.save()
            request.session['success_message']='Event created successfully'
            event.add_event_to_gcal()
            event.notify_publicity()
            tweet_option = form.cleaned_data.pop('tweet_option','N')
            if tweet_option=='T':
                event.tweet_event(False)
            elif tweet_option=='H':
                event.tweet_event(True)
            return redirect('event_cal:list')

        else:
            request.session['error_message']='There were errors in the submitted event, please correct the errors noted below.'
    else:
        form = EventForm(prefix='event')
        formset= MultiShiftFormset(prefix='shift')
    dp_ids=['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-date'%(count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'dp_ids':dp_ids,
        'dp_ids_dyn':['date'],
        'prefix':'shift',
        'subnav':'admin',
        'submit_name':'Create Event',
        'form_title':'Multiple shift event creation',
        'help_text':'Easily create shifts with multiple, regularly spaced events. Simply specify the start and end time for each block of time and the shift length. Do not use this for electee interview creation, use the intended form.',
        'shift_title':'Shift days and time windows',
        'shift_help_text':'Shifts will be automatically created within the window you specify, for the duration you give. Note that if your duration does not line up with the end time, you may go longer than you planned.',
        'back_button':{'link':reverse('event_cal:calendar_admin'),'text':'To Calendar Admin'},
        'event_photos':EventPhoto.objects.all(),
#        'date_prefixes':[{'id_shift':['start_time_0','end_time_0']}],
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit']=True
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
def create_electee_interviews(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to create electee interviews'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,form=BaseEventForm,exclude=('completed','google_event_id','project_report','event_type','members_only','needs_carpool','use_sign_in','allow_advance_sign_up','needs_facebook_event','needs_flyer'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    active_type = EventCategory.objects.get(name='Conducted Interviews')
    electee_type = EventCategory.objects.get(name='Attended Interviews')
    if request.method == 'POST':
        form = EventForm(request.POST,prefix='event')
        formset = InterviewShiftFormset(request.POST,prefix='shift')
        if form.is_valid() and formset.is_valid():
            active_event = form.save(commit=False)
            active_event.event_type=active_type
            active_event.save()
            active_id = active_event.id
            form.save_m2m()
            leaders = active_event.leaders.all()
            electee_event = active_event
            electee_event.pk=None
            electee_event.save()
            active_event=CalendarEvent.objects.get(id=active_id)
            electee_event.event_type=electee_type
            electee_event.leaders=leaders
            electee_event.name+=' (Electees)'
            active_event.name+=' (Actives)'
            active_event.save()
            electee_event.save()
            for shift_form in formset:
                if not shift_form.is_valid():
                    continue
                cleaned_data=shift_form.cleaned_data
                shift_date=cleaned_data['date']
                shifts_start = cleaned_data['start_time']
                mid_time =datetime.combine(shift_date,shifts_start)
                end_time = datetime.combine(shift_date,shift_form.cleaned_data['end_time']) 
                while mid_time<end_time:
                    start_time = mid_time
                    mid_time +=timedelta(minutes=shift_form.cleaned_data['duration'])
                    electee_shift = EventShift()
                    electee_shift.start_time = timezone.make_aware(start_time,timezone.get_current_timezone())
                    electee_shift.end_time = timezone.make_aware(mid_time,timezone.get_current_timezone())
                    electee_shift.location = shift_form.cleaned_data['location']
                    interview_type=shift_form.cleaned_data['interview_type']
                    if interview_type=='U' or interview_type=='UI':
                        electee_shift.ugrads_only = True
                    elif interview_type=='G' or interview_type=='GI':
                        electee_shift.grads_only = True
                    electee_shift.max_attendance = 1
                    electee_shift.electees_only = True
                    electee_shift.event = electee_event
                    electee_shift.save()
                    electee_shift_id=electee_shift.id
                    active_shift = electee_shift
                    active_shift.pk = None
                    active_shift.save()
                    active_shift.max_attendance = 2
                    active_shift.electees_only = False
                    active_shift.actives_only = True
                    active_shift.event = active_event
                    if interview_type=='U':
                        active_shift.ugrads_only = True
                        active_shift.grads_only=False
                    elif interview_type=='G':
                        active_shift.grads_only = True
                        active_shift.ugrads_only=False
                    else:
                        active_shift.grads_only = False
                        active_shift.ugrads_only=False
                    active_shift.save()
                    interview_shift = InterviewShift()
                    interview_shift.interviewer_shift = active_shift
                    interview_shift.interviewee_shift = EventShift.objects.get(id=electee_shift_id)
                    interview_shift.term = active_event.term
                    interview_shift.save()
                    
            request.session['success_message']='Event created successfully'
            active_event.add_event_to_gcal()
            electee_event.add_event_to_gcal()
            tweet_option = form.cleaned_data.pop('tweet_option','N')
            if tweet_option=='T':
                event.tweet_event(False)
            elif tweet_option=='H':
                event.tweet_event(True)
            return redirect('event_cal:list')
            
        else:
            request.session['error_message']='There were errors in the submitted event, please correct the errors noted below.'
    else:
        form = EventForm(prefix='event')
        formset= InterviewShiftFormset(prefix='shift')
    dp_ids=['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-date'%(count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'dp_ids':dp_ids,
        'dp_ids_dyn':['date'],
        'prefix':'shift',
        'subnav':'admin',
        'submit_name':'Create Interview Slots',
        'form_title':'Electee Interview Slot Creation',
        'help_text':'Create the interview slots. Just one per session, separate events will be automatically created for actives and electees.\n Note: the \"Grad interviewee anyone interviewer\" option is discouraged due to the nature of the case studies.',
        'shift_title':'Shift days and time windows',
        'shift_help_text':'Shifts will be automatically created within the window you specify, for the duration you give. Note that if your duration does not line up with the end time, you may go longer than you planned.',
        'back_button':{'link':reverse('event_cal:calendar_admin'),'text':'To Calendar Admin'},
        'event_photos':EventPhoto.objects.all(),
#        'date_prefixes':[{'id_shift':['start_time_0','end_time_0']}],
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit']=True
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
def create_event(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create events'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,form=BaseEventForm,exclude=('completed','google_event_id','project_report'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    if request.method == 'POST':
        form = EventForm(request.POST,prefix='event')
        formset = EventShiftFormset(request.POST,prefix='shift')
        if form.is_valid():
            event = form.save(commit=False)
            formset = EventShiftFormset(request.POST,prefix='shift',instance=event)
            formset[0].empty_permitted=False
            if formset.is_valid():
                event.save()
                form.save_m2m()
                formset.save()
                request.session['success_message']='Event created successfully'
                event.add_event_to_gcal()
                event.notify_publicity()
                tweet_option = form.cleaned_data.pop('tweet_option','N')
                if tweet_option=='T':
                    event.tweet_event(False)
                elif tweet_option=='H':
                    event.tweet_event(True)
                if event.use_sign_in:
                    request.session['info_message']='Please create a sign-in for %s'%(unicode(event),)
                    event_id=int(event.id)
                    return redirect('event_cal:create_meeting_signin', event_id)
                else:
                    return redirect('event_cal:list')
            else:
                request.session['error_message']='Either there were errors in your shift(s) or you forgot to include one.'
        else:
            request.session['error_message']='There were errors in the submitted event, please correct the errors noted below.'
    else:
        form = EventForm(prefix='event')
        formset= EventShiftFormset(prefix='shift',instance=CalendarEvent())
    dp_ids=['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-start_time_0'%(count))
        dp_ids.append('id_shift-%d-end_time_0'%(count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'dp_ids':dp_ids,
        'dp_ids_dyn':['start_time_0', 'end_time_0'],
        'prefix':'shift',
        'subnav':'admin',
        'submit_name':'Create Event',
        'form_title':'Create New Event',
        'help_text':'',
        'shift_title':'Event Shifts',
        'shift_help_text':'',
        'back_button':{'link':reverse('event_cal:calendar_admin'),'text':'To Calendar Admin'},
        'event_photos':EventPhoto.objects.all(),
#        'date_prefixes':[{'id_shift':['start_time_0','end_time_0']}],
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit']=True
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def create_meeting_signin(request, event_id):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create meeting signins.'
        return get_previous_page(request,alternate='event_cal:list')
    e=get_object_or_404(CalendarEvent,id=event_id)
    if not e.use_sign_in:
        request.session['error_message']='You can only create a meeting signin for a meeting.'
        return get_previous_page(request,alternate='event_cal:list')
    MeetingSignInForm = modelform_factory(MeetingSignIn,exclude=('event',))
    if request.method == 'POST':
        form = MeetingSignInForm(request.POST)
        if form.is_valid():
            signin = form.save(commit=False)
            signin.event=e
            signin.save()
            request.session['success_message']='Event created successfully'
            return redirect('event_cal:list')
        else:
            request.session['error_message']='There were errors in the submitted meeting sign_in, please correct the errors noted below.'
    else:
        form = MeetingSignInForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Create  Sign-in',
        'back_button':{'link':reverse('event_cal:event_detail',args=[event_id]),'text':'To %s Page'%(e.name)},
        'form_title':'Add Sign in for %s'%(e.name),
        'help_text':'In order to use the sign-in feature, please create a sign-in form. Note that the form will automatically have an optional \"Free Response\" question in addition to the quick question you provide.',
#        'can_add_row':False,
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


def delete_event(request, event_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    if Permissions.can_edit_event(e,request.user) and not e.completed:
        e.delete_gcal_event()
        e.delete()
        request.session['success_message']='Event deleted successfully'
        return redirect('event_cal:list')
    else:
        request.session['error_message']='You do not have sufficient permissions to delete this event, or it has already been completed.'
        return redirect('event_cal:index')

def delete_shift(request,event_id, shift_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    s= get_object_or_404(EventShift,id=shift_id)
    if Permissions.can_edit_event(e,request.user):
        s.delete_gcal_event_shift()
        s.delete()
        request.session['event_signed_up']=int(event_id)
        request.session['success_message']='Event shift deleted successfully'
        return get_previous_page(request,alternate='event_cal:list')
    else:
        request.session['error_message']='You do not have sufficient permissions to delete this shift.'
        return redirect('even_cal:index')

def email_participants(request,event_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    if not Permissions.can_edit_event(e,request.user) or not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You are not authorized to email this event\'s participants.'
        return get_previous_page(request,alternate='event_cal:list')
    if request.method == 'POST':
        form = EventEmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body']
            e.email_participants(subject,body,request.user.userprofile.memberprofile)
            request.session['success_message']='Event participants emailed successfully'
            return redirect('event_cal:event_detail',event_id)
        else:
            request.session['error_message']='You need to include a subject and a body.'
    else:
        form = EventEmailForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Email Participants',
        'form_title':'Specify Subject/Body for Emailing Participants',
        'help_text':'Use this form to email all current event participants. Event leaders will be cc\'ed and you will be the reply-to address.',
        'base':'event_cal/base_event_cal.html',
        'back_button':{'link':reverse('event_cal:event_detail',args=[event_id]),'text':'To  %s Page'%(e.name)},
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
def edit_event(request, event_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    if not Permissions.can_edit_event(e,request.user):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,form=BaseEventForm,exclude=('completed','google_event_id','project_report'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    needed_flyer = e.needs_flyer
    needed_facebook =e.needs_facebook_event
    if request.method == 'POST':
        form = EventForm(request.POST,prefix='event',instance=e)
        formset = EventShiftEditFormset(request.POST,prefix='shift',instance=e)
        if form.is_valid():
            event = form.save(commit=False)
            formset = EventShiftEditFormset(request.POST,prefix='shift',instance=event)
            formset[0].empty_permitted=False
            if formset.is_valid():
                event.save()
                form.save_m2m()
                formset.save()
                event.add_event_to_gcal()
                tweet_option = form.cleaned_data.pop('tweet_option','N')
                if tweet_option=='T':
                    event.tweet_event(False)
                elif tweet_option=='H':
                    event.tweet_event(True)
                event.notify_publicity(needed_flyer =needed_flyer,needed_facebook=needed_facebook,edited=True)
                request.session['success_message']='Event updated successfully'
                return redirect('event_cal:event_detail',event_id)
            else:
                request.session['error_message']='Either there were errors in your shift(s) or you forgot to include one.'
        else:
            request.session['error_message']='There were errors in the submitted event, please correct the errors noted below.'
    else:
        form = EventForm(prefix='event',instance=e)
        formset= EventShiftEditFormset(prefix='shift',instance=e)
    dp_ids=['id_event-announce_start']
    for count in range(len(formset)):
        dp_ids.append('id_shift-%d-start_time_0'%(count))
        dp_ids.append('id_shift-%d-end_time_0'%(count))
    template = loader.get_template('event_cal/detail.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'edit':True,
        'event':e,
        'dp_ids':dp_ids,
        'dp_ids_dyn':['start_time_0', 'end_time_0'],
        'prefix':'shift',
        'subnav':'list',
        'submit_name':'Submit Changes',
        'shift_title':'Edit Shifts',
        'event_photos':EventPhoto.objects.all(),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit']=True
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def update_completed_event(request, event_id):
    e = get_object_or_404(CalendarEvent,id=event_id)
    if not Permissions.can_edit_event(e,request.user):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.can_complete_event():
        request.session['error_message'] = 'This event hasn\'t been completed yet. Do that first.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.is_fixed_progress():
        form_type = CompleteFixedProgressEventFormSet
        is_fixed = True
    else:
        form_type = CompleteEventFormSet
        is_fixed = False
    form_prefix='update_event'
    if request.method == 'POST':
        formset = form_type(request.POST,prefix='update_event',queryset=ProgressItem.objects.filter(related_event=e))
        if formset.is_valid():
            instances = formset.save(commit=False)
            first_shift=e.eventshift_set.all()[0]
            duplicate_progress = set()
            for instance in instances:
                if not instance.member.is_member():
                    continue
                if instance not in [item[0] for item in formset.changed_objects if item[0]==instance]:   
                    # double check they don't already have progress?
                    if not e.eventshift_set.filter(attendees=instance.member).exists():
                        first_shift.attendees.add(instance.member)
                        first_shift.save()
                    if ProgressItem.objects.filter(related_event=e,member=instance.member).exists():
                        duplicate_progress|=set([instance.member])
                        continue
                    instance.term=AcademicTerm.get_current_term()
                    instance.event_type=e.event_type
                    instance.date_completed=date.today()
                    instance.related_event=e
                    instance.name=e.name
                if is_fixed:
                    instance.amount_completed=1
                instance.save()
            for instance in formset.deleted_objects:
                for shift in e.eventshift_set.filter(attendees=instance.member):
                    shift.attendees.remove(instance.member)
                    shift.save()
                    
            if duplicate_progress:
                request.session['warning_message']='The following members had progress listed twice, with latter listings ignored: '+ ','.join([prof.uniqname for prof in duplicate_progress])+'. Go to update progress to check that the amount of progress is correct'
            request.session['success_message']='Event and progress updated successfully'
            return redirect('event_cal:event_detail',event_id)
        else:
            request.session['error_message']='There were errors in your submission. Progress was not updated. Please correct the errors and try again.'
    else:
        formset = form_type(prefix='update_event',queryset=ProgressItem.objects.filter(related_event=e).order_by('member__last_name'))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':form_prefix,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Update Event',
        'back_button':{'link':reverse('event_cal:event_detail',args=[event_id]),'text':'To  %s Page'%(e.name)},
        'form_title':'Update Completion Report for  %s'%(e.name),
        'help_text':'Note that this is *not* the project report. Use this to update the progress of an event that has already been completed. Those with progress are listed below.',
        'can_add_row':True,
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
## change it so that the form has an extra column that is whether or not they signed in
# include the attendees as options as well
def complete_event(request, event_id):
    e = get_object_or_404(CalendarEvent,id=event_id)
    if not Permissions.can_edit_event(e,request.user):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if not e.can_complete_event():
        request.session['error_message'] = 'This event can\'t be completed yet.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.is_fixed_progress():
        form_type = CompleteFixedProgressEventFormSet
        is_fixed = True
    else:
        form_type = CompleteEventFormSet
        is_fixed = False
    form_prefix='complete_event'
    if request.method == 'POST':
        formset = form_type(request.POST,prefix=form_prefix,queryset=ProgressItem.objects.none())
        if formset.is_valid():
            instances = formset.save(commit=False)
            first_shift=e.eventshift_set.all()[0]
            duplicate_progress = set()
            for instance in instances:
                if not instance.member.is_member():
                    continue
                # double check they don't already have progress?
                if not e.eventshift_set.filter(attendees=instance.member).exists():
                    first_shift.attendees.add(instance.member)
                    first_shift.save()
                if ProgressItem.objects.filter(related_event=e,member=instance.member).exists():
                    duplicate_progress|=set([instance.member])
                    continue
                instance.term=AcademicTerm.get_current_term()
                instance.event_type=e.event_type
                instance.date_completed=date.today()
                instance.related_event=e
                instance.name=e.name
                if is_fixed:
                    instance.amount_completed=1
                instance.save()
            confirmed_attendees=MemberProfile.objects.filter(progressitem__related_event=e)
            for shift in e.eventshift_set.all():
                for attendee in shift.attendees.exclude(pk__in=confirmed_attendees):
                    if attendee.is_member():
                        shift.attendees.remove(attendee)
                shift.save()
            e.completed=True
            e.save()
            if duplicate_progress:
                request.session['warning_message']='The following members had progress listed twice, with latter listings ignored: '+ ','.join([prof.uniqname for prof in duplicate_progress])+'. Go to update progress to check that the amount of progress is correct'
            request.session['success_message']='Event and progress updated successfully'
            request.session['project_report_event']=event_id
            return redirect('event_cal:event_project_report',event_id)
        else:
            request.session['error_message']='There were errors in your submission. Progress was not updated. Please correct the errors and try again.'
    else:
        # create initial
        initial=[]
        attendees = UserProfile.objects.filter(event_attendee__event=e).distinct()
        for attendee in attendees.order_by('last_name'):
            if not attendee.is_member():
                continue
            if ProgressItem.objects.filter(related_event=e,member=attendee.memberprofile).exists():
                continue
            if is_fixed:
                initial.append({'member':attendee.memberprofile})
            else:
                initial.append({'member':attendee.memberprofile,'amount_completed':round(e.get_attendee_hours_at_event(attendee),2)})
        form_type.extra=len(initial)+1
        formset = form_type(prefix=form_prefix,queryset=ProgressItem.objects.none(),initial=initial)
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':form_prefix,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Complete Event',
        'back_button':{'link':reverse('event_cal:event_detail',args=[event_id]),'text':'To  %s Page'%(e.name)},
        'form_title':'Completion Report for  %s'%(e.name),
        'help_text':'Note that this is *not* the project report. Use this to assign progress for those who attended the event. The list of those who signed up for the event, as well as the number of hours they signed up for, is included below. Please make any changes necessary and then click the complete event button. If the event uses a sign-in feature, only those who signed up in advance but did not sign in are included below. Those who signed in have already had their progress assigned.',
        'can_add_row':True,
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


def generate_announcements(request):
    if not Permissions.can_generate_announcements(request.user):
        request.session['error_message']='You are not authorized to generate the weekly announcements.'
        return get_previous_page(request,alternate='event_cal:index')
    request.session['current_page']=request.path
    now = timezone.now()
    announcement_parts = AnnouncementBlurb.objects.filter(start_date__lte=now.date).filter(end_date__gt=now.date)
    template = loader.get_template('event_cal/announcements.html')
    context_dict = {
        'announcement_parts':announcement_parts,
        'subnav':'admin',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def add_announcement(request):
    if not Permissions.can_add_announcements(request.user):
        request.session['error_message']='You are not authorized to contribute weekly announcements.'
        return get_previous_page(request,alternate='event_cal:index')
    AnnouncementForm = modelform_factory(AnnouncementBlurb,form=BaseAnnouncementForm)
    if request.method =='POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            form.save()
            request.session['success_message']='Announcement(s) submitted successfully'
            return get_previous_page(request,alternate='event_cal:index')          
        else:
            request.session['error_message']='There were errors in your submission, please correct them and resubmit. Your submission was not saved.'
    else:
        form = AnnouncementForm()
    dp_ids=['id_start_date','id_end_date']
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'dp_ids':dp_ids,
        'subnav':'admin',
        'has_files':False,
        'submit_name':'Submit Announcement',
        'form_title':'Add an Announcement Section',
        'help_text':'Add an announcement to be included in the weekly email summary. Do not submit announcements for events. Those are automatically included using the information provided in the event details.',
        'base':'event_cal/base_event_cal.html',
        'back_button':{'link':reverse('event_cal:calendar_admin'),'text':'To Calendar Admin'},
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def gcal_test(request):
    if not request.user.is_superuser:
        raise PermissionDenied()
    c = get_credentials()
    if c is None or c.invalid:
        return initialize_gcal()
    else:
        request.session['warning_message']='Current Credentials still valid, re-authentication unnecessary.'
        return get_previous_page(request,alternate='event_cal:index')

def oauth(request):
    code = request.GET.get('code',None)
    process_auth(code)

    return get_previous_page(request,alternate='event_cal:list')

def event_project_report(request,event_id):
    e=get_object_or_404(CalendarEvent,id=event_id)
    request.session['project_report_event']=event_id
    request.session.pop('project_report_non_event',None)
    request.session.pop('project_report_id',None)
    return project_report(request)
def project_report_by_id(request,report_id):
    request.session.pop('project_report_event',None)
    request.session.pop('project_report_non_event',None)
    request.session['project_report_id']=report_id
    return project_report(request)

def non_event_project_report(request,ne_id):
    request.session.pop('project_report_event',None)
    request.session.pop('project_report_id',None)
    request.session['project_report_non_event']=ne_id
    return project_report(request)

def project_report(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create project reports.'
        return get_previous_page(request,alternate='event_cal:index')
    related_event = request.session.pop('project_report_event',None)
    related_non_event = request.session.pop('project_report_non_event',None)
    report_id = request.session.pop('project_report_id',None)
    if related_event:
        event = CalendarEvent.objects.get(id=related_event)
        event_name=event.name
        if event.project_report:
            event_name=event.project_report.name
        ProjectReportForm =modelform_factory(ProjectReport,exclude=('term',))
    elif related_non_event:
        non_event = NonEventProject.objects.get(id=related_non_event)
        event_name=non_event.name
        if non_event.project_report:
            event_name=non_event.project_report.name
        ProjectReportForm =modelform_factory(ProjectReport,exclude=('term',))
    elif report_id:
        report = get_object_or_404(ProjectReport,id=report_id)
        event_name=report.name
        ProjectReportForm =modelform_factory(ProjectReport,exclude=('term',))
    else:
        event_name = 'Unspecified Event'
        ProjectReportForm = modelform_factory(ProjectReport)

    if request.method =='POST':
        if related_event and event.project_report:
            form = ProjectReportForm(request.POST,instance=event.project_report)
        elif related_non_event and non_event.project_report:
            form = ProjectReportForm(request.POST,instance=non_event.project_report)
        elif report_id:
            form = ProjectReportForm(request.POST,instance=report)
        else:
            form = ProjectReportForm(request.POST)
        
        if form.is_valid():
            if related_event:
                pr = form.save(commit=False)
                event= CalendarEvent.objects.get(id=related_event)
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
                pr=form.save()
            else:
                pr = form.save()
                request.session['warning_message']='Project report not attached to event, please fix this.'
            request.session['success_message']='Project report created successfully'
            return redirect('event_cal:index')
        else:
            request.session['error_message']='Project report contained errors, was not saved.'
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
    dp_ids=['id_planning_start_date']
    context_dict ={
        'form':form,
        'dp_ids':dp_ids,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Create/update project report',
        'form_title':'Create project report for %s'%(event_name),
        'help_text':'These are reports sent to the national organization to determine eligibility for certain chapter awards. They are also used for transition material to help future project leaders perform a similar event. Please be descriptive in your responses.',
        'base':'event_cal/base_event_cal.html',
        }
    if related_event:
        request.session['project_report_event']=related_event
    if related_non_event:
        request.session['project_report_non_event']=related_non_event
    if report_id:
        request.session['project_report_id']=report_id
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
    

def submit_tutoring_form(request):
    is_member=False
    if hasattr(request.user,'userprofile'):
        if request.user.userprofile.is_member():
            is_member=True
            profile = request.user.userprofile.memberprofile

    if not is_member:
        request.session['error_message']='You must be logged in, have a profile, and be a member to submit a tutoring form.'
        return get_previous_page(request,alternate='event_cal:index')
    TutoringForm = modelform_factory(TutoringRecord, exclude=('approved','tutor',))
    tutoring_chair = OfficerPosition.objects.filter(name='Campus Outreach Officer')
    current_chair = Officer.objects.filter(position__name='Campus Outreach Officer',term=AcademicTerm.get_current_term()).distinct()
    if current_chair.exists():
        tutoring_chair_name = current_chair[0].user.get_firstlast_name()+'\n'
    else:
        tutoring_chair_name=''
    if tutoring_chair.exists():
        tutoring_email=tutoring_chair[0].email
        tutoring_name = tutoring_chair[0].name
    else:
        tutoring_email='tbp.campusoutreach@umich.edu'
        tutoring_name='Campus Outreach Officer'
    if request.method =='POST':
        form = TutoringForm(request.POST)
        if form.is_valid():
            tutoring_record = form.save(commit=False)
            tutoring_record.tutor = profile
            tutoring_record.approved = False
            tutoring_record.save()
            request.session['success_message']='Tutoring Form submitted successfully'
            #TODO move these to a more sensible location and use kyle & my email script
            recipient = tutoring_record.student_uniqname
            tutor_name = tutoring_record.tutor.get_firstlast_name()
            recipient_email = recipient+"@umich.edu"
            number_hours_str = str(tutoring_record.number_hours)
            number_hours = number_hours_str.rstrip('0').rstrip('.') if '.' in number_hours_str else number_hours_str
            body = r'''Hello!
            
%(tutor)s logged that you were tutored for %(hours)s hours on %(date)s. We'd like to know how it went. If you have any feedback for us we invite you to fill out an (anonymous) feedback form: http://tinyurl.com/TBPtutoringSurvey

If you have any other questions about tutoring, please feel free to email me at %(email)s,
            
Regards,
%(chair_name)s%(position_name)s
%(email)s

Note: This is an automated email. Please do not reply to it as responses are not checked.'''%{'tutor':tutor_name,'hours':number_hours,'date':unicode(tutoring_record.date_tutored),'email':tutoring_email,'chair_name':tutoring_chair_name,'position_name':tutoring_name,}
            send_mail('We want your feedback on your recent tutoring session.',body,tutoring_email,[recipient_email],fail_silently=True)
            return get_previous_page(request,alternate='event_cal:index')          
        else:
            request.session['error_message']='There were errors in your submission, please correct them and resubmit. Your submission was not saved.'
    else:
        form = TutoringForm()
    dp_ids=['id_date_tutored']
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'dp_ids':dp_ids,
        'subnav':'tutoring_form',
        'has_files':False,
        'submit_name':'Submit Tutoring Form',
        'form_title':'Tutoring Summary Form',
        'help_text':'Please log your tutoring here. By submitting this form, you attest that you tutored the student for the claimed number of hours. Note that the student will be emailed and given the opportunity to provide anonymous feedback.',
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


def add_project_report_to_event(request,event_id):
    event=get_object_or_404(CalendarEvent,id=event_id)
    if not Permissions.can_edit_event(event,request.user):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:index')

    if request.method =='POST':
        form = AddProjectReportForm(request.POST)
        form.fields['report'].queryset = Permissions.project_reports_you_can_view(request.user)
        if form.is_valid():
            report = form.cleaned_data.pop('report',None)
            if report:
                event.project_report=report
                event.save()
            request.session['success_message']='Project Report attached successfully.'
            return get_previous_page(request,alternate='event_cal:index')          
        else:
            request.session['error_message']='There were errors in your submission, please correct them and resubmit. Your submission was not saved.'
    else:
        initial={'report':event.project_report}
        form = AddProjectReportForm(initial=initial)
        form.fields['report'].queryset = Permissions.project_reports_you_can_view(request.user)
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'list',
        'has_files':False,
        'submit_name':'Add/Update Attached Report',
        'form_title':'Attach project report to %s'%(event.name),
        'help_text':'You may have several events that share a common project report. Use this form to attach an existing project report to this event.',
        'base':'event_cal/base_event_cal.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def calendar_admin(request):
    if not Permissions.can_view_calendar_admin(request.user):
        request.session['error_message']='You are not authorized to access calendar admin functionality.'
        return get_previous_page(request,alternate='event_cal:index')
    request.session['current_page']=request.path
    template = loader.get_template('event_cal/calendar_admin.html')
    links=[]
    if Permissions.can_create_events(request.user):
        links.append({'link':reverse('event_cal:create_event'),'name':'Add Event'})
        links.append({'link':reverse('event_cal:create_multishift_event'),'name':'Add Event with many shifts'})
    if Permissions.can_add_announcements(request.user):
        links.append({'link':reverse('event_cal:add_announcement'),'name':'Add Announcement'})
    if Permissions.can_generate_announcements(request.user):
        links.append({'link':reverse('event_cal:generate_announcements'),'name':'Generate Announcements'})
        links.append({'link':reverse('event_cal:edit_announcements'),'name':'Edit Announcements'})
    if Permissions.can_add_event_photo(request.user):
        links.append({'link':reverse('event_cal:add_event_photo'),'name':'Add Event Photo'})
    if Permissions.can_manage_electee_progress(request.user):
        links.append({'link':reverse('event_cal:create_electee_interviews'),'name':'Schedule Electee Interview Slots'})
    context_dict = {
        'subnav':'admin',
        'page_title':'Calendar Administrative Functions',
        'links':links,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def edit_announcements(request):
    if not Permissions.can_generate_announcements(request.user):
        request.session['error_message']='You are not authorized to edit announcements.'
        return get_previous_page(request,alternate='event_cal:index')
    request.session['current_page']=request.path
    now = timezone.now()
    announcement_parts = AnnouncementBlurb.objects.filter(end_date__gt=now.date)
    AnnouncementFormSet = modelformset_factory(AnnouncementBlurb)
    if request.method == 'POST':
        formset = AnnouncementFormSet(request.POST,prefix='announcements',queryset=announcement_parts)
        if formset.is_valid():
            formset.save()
            request.session['success_message']='The announcements were successfully updated.'
            return redirect('event_cal:calendar_admin')
        else:
            request.session['error_message']='There were errors in your submission. The changes were not saved. Please correct the errors and try again.'
    else:
        formset = AnnouncementFormSet(prefix='announcements',queryset=announcement_parts)
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'admin',
        'has_files':False,
        'can_add_row':True,
        'submit_name':'Update Announcements',
        'form_title':'Edit Submitted Announcements',
        'help_text':'Edit announcements for the current/future announcement cycles.',
        'base':'event_cal/base_event_cal.html',
        'back_button':{'link':reverse('event_cal:calendar_admin'),'text':'To Calendar Admin'},
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
