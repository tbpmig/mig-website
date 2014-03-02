# Create your views here.
from datetime import datetime,date,timedelta

from django.utils import timezone
from django.utils.encoding import force_unicode
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
from markdown import markdown

from event_cal.forms import  EventShiftFormset, EventShiftEditFormset,CompleteEventFormSet, MeetingSignInForm, CompleteFixedProgressEventFormSet,EventFilterForm,AddProjectReportForm
from event_cal.models import GoogleCalendar,CalendarEvent, EventShift, MeetingSignIn, MeetingSignInUserData,AnnouncementBlurb,CarpoolPerson,EventPhoto
from history.models import ProjectReport, Officer
from mig_main.default_values import get_current_term
from mig_main.models import OfficerPosition,PREFERENCES,UserPreference,MemberProfile,get_members
from mig_main.utility import get_previous_page, Permissions, get_message_dict
from outreach.models import TutoringRecord
from requirements.models import ProgressItem, EventCategory
#from requirements.models import SemesterType

from event_cal.gcal_functions import initialize_gcal, process_auth,get_credentials,get_authorized_http,get_service

GCAL_USE_PREF = [d for d in PREFERENCES if d.get('name') == 'google_calendar_add'][0]
GCAL_ACCT_PREF = [d for d in PREFERENCES if d.get('name') == 'google_calendar_account'][0]

before_grace = timedelta(minutes=-30)
after_grace = timedelta(hours = 1)

def delete_gcal_event(event):
    c = get_credentials()
    h = get_authorized_http(c)
    if h:
        service = get_service(h)
        for shift in event.eventshift_set.all():
            if shift.google_event_id:
                try:
                    service.events().delete(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id).execute()
                except:
                    pass
def delete_gcal_event_shift(event,shift):
    c = get_credentials()
    h = get_authorized_http(c)
    if h:
        service = get_service(h)
        if shift.google_event_id:
            try:
                service.events().delete(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id).execute()
            except:
                pass
def add_event_to_gcal(event):
    c = get_credentials()
    h = get_authorized_http(c)
    if h:
        service = get_service(h)
        for shift in event.eventshift_set.all():
            new_event = True
            if shift.google_event_id:
                try:
                    gcal_event = service.events().get(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id).execute()
                    if gcal_event['status']=='cancelled':
                        gcal_event={}
                        new_event = True
                    else:
                        gcal_event['sequence']=gcal_event['sequence']+1
                        new_event = False
                except:
                    gcal_event = {}
            else:
                gcal_event = {}
            gcal_event['summary']=event.name
            gcal_event['location']=shift.location
            gcal_event['start']={'dateTime':shift.start_time.isoformat('T'),'timeZone':'America/Detroit'}
            gcal_event['end']={'dateTime':shift.end_time.isoformat('T'),'timeZone':'America/Detroit'}
            gcal_event['recurrence']=[]
            gcal_event['description']=markdown(force_unicode(event.description),['nl2br'],safe_mode=True,enable_attributes=False)
            if not new_event :
                service.events().update(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id,body=gcal_event).execute()
            else:
                submitted_event=service.events().insert(calendarId=event.google_cal.calendar_id,body=gcal_event).execute()
                shift.google_event_id=submitted_event['id']
                shift.save()

def add_attendee_to_gcal(name,email,event,shift):
    c = get_credentials()
    h = get_authorized_http(c)
    if h:
        service = get_service(h)
        if not shift.google_event_id:
            return
        gcal_event = service.events().get(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id).execute()
        if gcal_event['status']=='cancelled':
            return
        else:
            gcal_event['sequence']+=1
            if 'attendees' in gcal_event:
                gcal_event['attendees'].append(
                    {
                        'email':email,
                        'displayName':name,
                    })
            else:
                gcal_event['attendees']=[{
                        'email':email,
                        'displayName':name,
                    }]
                
            service.events().update(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id,body=gcal_event).execute()
            
def delete_gcal_attendee(email,event,shift):
    c = get_credentials()
    h = get_authorized_http(c)
    if h:
        service = get_service(h)
        if not shift.google_event_id:
            return
        try:
            gcal_event = service.events().get(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id).execute()
            if gcal_event['status']=='cancelled':
                return
            else:
                gcal_event['sequence']+=1
                if 'attendees' in gcal_event:
                    gcal_event['attendees'][:]=[a for a in gcal_event['attendees'] if a.get('email') !=email]
                    service.events().update(calendarId=event.google_cal.calendar_id,eventId=shift.google_event_id,body=gcal_event).execute()
        except:
            return        

def get_event_category_children(query,category):
    for child in category.eventcategory_set.all():
        query|=get_event_category_children(query,child)
    return query|Q(event_type=category)

def flatten_category_tree(category,depth):
    if category:
        category_array=[{'category':category,'depth':depth}]
        for child in category.eventcategory_set.all():
            category_array+=flatten_category_tree(child,depth+1)
    else:
        category_array=[]
        for parentless_category in EventCategory.objects.filter(parent_category=None):
            category_array+=flatten_category_tree(parentless_category,depth+1)
    return category_array

    
def get_permissions(user):
    return {'can_add_event':Permissions.can_create_events(user),
        'can_add_announcements':Permissions.can_add_announcements(user),
        'can_generate_announcements':Permissions.can_generate_announcements(user),
        'can_submit_tutoring_form':(hasattr(user,'userprofile') and user.userprofile.is_member()),
        'can_add_event_photo':(hasattr(user,'userprofile') and user.userprofile.is_member()),}
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'now':timezone.localtime(timezone.now()),
        'upcoming_events':get_upcoming_events(),
        'before_grace':before_grace,
        'after_grace':after_grace,
        'edit_page':False,
        })
    return context_dict

def can_complete_event(event):
    s = event.eventshift_set
    now = timezone.now()
    s_future = s.filter(end_time__gte=now)
    if event.completed:
        return False
    if s_future:
        return False
    else:
        return True
def can_edit_event(user,event):
    try:
        if hasattr(user,'userprofile') and user.userprofile.memberprofile in event.leaders.all():
            return True
        else:
            return Permissions.can_delete_events(user)
    except ObjectDoesNotExist:
        return False
def get_current_meeting_query():
    now = timezone.localtime(timezone.now())
    return Q(use_sign_in=True)&Q(eventshift__end_time__gte=(now-after_grace))&Q(eventshift__start_time__lte=(now-before_grace))
def get_upcoming_events():
    now = timezone.localtime(timezone.now())
    today=date.today()
    non_meeting_query = Q(eventshift__start_time__gte=now)&Q(announce_start__lte=today)
    meeting_query = get_current_meeting_query()
    not_officer_meeting = ~Q(event_type__name='Officer Meetings')
    upcoming_events = CalendarEvent.objects.filter((non_meeting_query|meeting_query)&not_officer_meeting).distinct().annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift')
    return upcoming_events
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
                                    user_data.free_response='no response give'
                            user_data.save()
                        hours = (shift.end_time-shift.start_time).seconds/3600.0
                        if event.is_fixed_progress():
                            hours = 1
                        p=ProgressItem(member=profile.memberprofile,term=get_current_term(),amount_completed=hours,event_type=event.event_type,related_event=event,date_completed=date.today(),name=event.name)
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
    template = loader.get_template('event_cal/meeting_signin.html')
    context_dict = {
        'event':event,
        'shift':shift,
        'form':form,
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
        'can_edit_event':can_edit_event(request.user,event),
        'can_add_sign_in':(Permissions.can_create_events(request.user) and not MeetingSignIn.objects.filter(event=event).exists() and event.use_sign_in),
        'can_complete':(can_complete_event(event) and can_edit_event(request.user,event)),
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
            if request.user.userprofile.is_member or not event.members_only: 
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
                    add_attendee_to_gcal(request.user.userprofile.get_firstlast_name(),email_to_use,event,shift)

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
            delete_gcal_attendee(email_to_use,event,shift)
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
    template = loader.get_template('event_cal/carpool_sign_up.html')
    context_dict = {
        'event':event,
        'form':form,
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
    if Permissions.can_create_events(request.user):
        EventPhotoForm = modelform_factory(EventPhoto)
    else:
        EventPhotoForm = modelform_factory(EventPhoto,exclude=('project_report',))
    if request.method =='POST':
        form = EventPhotoForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            request.session['success_message']='Photo successfully submitted'
            return get_previous_page(request,alternate='event_cal:index')
        else:
            request.session['warning_message']='There were errors in your submission'
    else:
        form = EventPhotoForm()
    template = loader.get_template('event_cal/add_event_photo.html')
    context_dict = {
        'form':form,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
        
def list(request):
    # add a form to filter the events
    request.session['current_page']=request.path
    user_is_member = False
    has_profile = False
    event_signed_up = request.session.pop('event_signed_up',None)
    query_semester = Q(term=get_current_term())
    query_members = Q(members_only=False) 
    query_event_type=Q()
    query_location=Q()
    selected_boxes = []
    request.session['info_message']='Only events in the current semester are shown. To view other events consult with the website officer.'
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
            event_categories = form.cleaned_data['event_reqs']
            for category in event_categories:
                selected_boxes.append(category.id)
                query_event_type=get_event_category_children(query_event_type,category)
    else:
        now = timezone.localtime(timezone.now())
        starting_after_text=date.today().isoformat()
        query_date=Q(eventshift__end_time__gte=now)  
        if not Permissions.view_officer_meetings_by_default(request.user):
            query_event_type = ~Q(event_type__name='Officer Meetings')
        initial={'after_date':starting_after_text}
        form = EventFilterForm(initial=initial)
    events = CalendarEvent.objects.filter(query_members&query_semester&query_date&query_event_type&query_location).distinct()
    template = loader.get_template('event_cal/list.html')
    packed_events=[]
    for event in events.annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift'):
        packed_events.append({'event':event,'can_edit':can_edit_event(request.user,event)})
    context_dict = {
        'events':packed_events,
        'user_is_member':user_is_member,
        'has_profile':has_profile,
        'event_signed_up':event_signed_up,
        'form':form,
        'dp_ids':['dp_before','dp_after'],
        'sorted_event_categories':flatten_category_tree(None,0),
        'selected_boxes':selected_boxes,
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
        my_events = CalendarEvent.objects.filter(eventshift__attendees__uniqname=request.user.userprofile.uniqname).distinct().annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift')

        events_im_leading = CalendarEvent.objects.filter(leaders__uniqname=request.user.userprofile.uniqname).distinct().annotate(earliest_shift=Min('eventshift__start_time')).order_by('earliest_shift')

    template = loader.get_template('event_cal/my_events.html')
    packed_events=[]
    for event in my_events:
        packed_events.append({'event':event,'can_edit':can_edit_event(request.user,event)})
    context_dict = {
        "my_events":packed_events,
        "events_im_leading":events_im_leading,
        'has_profile':has_profile,
        'event_signed_up':event_signed_up,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def create_event(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create events'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,exclude=('completed','google_event_id','project_report'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['leaders'].queryset=get_members().order_by('last_name')
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
                add_event_to_gcal(event)
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
#    for count in range(len(formset)):
        #dp_ids.append('id_shift-%d-start_time_0'%(count))
        #dp_ids.append('id_shift-%d-end_time_0'%(count))
    template = loader.get_template('event_cal/create_event.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'dp_ids':dp_ids,
        'prefix':'shift',
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
    template = loader.get_template('event_cal/create_meeting_signin.html')
    context_dict = {
        'form':form,
        'event':e,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


def delete_event(request, event_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    if can_edit_event(request.user,e) and not e.completed:
        delete_gcal_event(e)
        e.delete()
        request.session['success_message']='Event deleted successfully'
        return redirect('event_cal:list')
    else:
        request.session['error_message']='You do not have sufficient permissions to delete this event, or it has already been completed.'
        return redirect('event_cal:index')

def delete_shift(request,event_id, shift_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    s= get_object_or_404(EventShift,id=shift_id)
    if can_edit_event(request.user,e):
        delete_gcal_event_shift(e,s)
        s.delete()
        request.session['event_signed_up']=int(event_id)
        request.session['success_message']='Event shift deleted successfully'
        return get_previous_page(request,alternate='event_cal:list')
    else:
        request.session['error_message']='You do not have sufficient permissions to delete this shift.'
        return redirect('even_cal:index')


def edit_event(request, event_id):
    e= get_object_or_404(CalendarEvent,id=event_id)
    if not can_edit_event(request.user,e):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:list')
    request.session['current_page']=request.path
    EventForm = modelform_factory(CalendarEvent,exclude=('completed','google_event_id','project_report'))
    EventForm.base_fields['assoc_officer'].queryset=OfficerPosition.objects.filter(enabled=True)
    EventForm.base_fields['assoc_officer'].label = 'Associated Officer'
    
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
                add_event_to_gcal(event)
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
#    for count in range(len(formset)):
#        dp_ids.append('id_shift-%d-start_time_0'%(count))
#        dp_ids.append('id_shift-%d-end_time_0'%(count))
    template = loader.get_template('event_cal/detail.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'edit':True,
        'event':e,
        'dp_ids':dp_ids,
        'prefix':'shift',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context_dict['edit']=True
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def update_completed_event(request, event_id):
    e = get_object_or_404(CalendarEvent,id=event_id)
    if not can_edit_event(request.user,e):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if can_complete_event(e):
        request.session['error_message'] = 'This event hasn\'t been completed yet. Do that first.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.is_fixed_progress():
        form_type = modelformset_factory(ProgressItem,exclude=('term','event_type','date_completed','amount_completed','related_event','name'),can_delete=True)
        is_fixed = True
    else:
        form_type = modelformset_factory(ProgressItem,exclude=('term','event_type','date_completed','related_event','name',),can_delete=True)
        is_fixed = False
    form_prefix='update_event'
    if request.method == 'POST':
        formset = form_type(request.POST,prefix='update_event',queryset=ProgressItem.objects.filter(related_event=e))
        if formset.is_valid():
            instances = formset.save(commit=False)
            first_shift=e.eventshift_set.all()[0]
            for instance in instances:
                if not instance.member.is_member():
                    continue
                if instance not in [item[0] for item in formset.changed_objects if item[0]==instance]:   
                    # double check they don't already have progress?
                    if not e.eventshift_set.filter(attendees=instance.member).exists():
                        first_shift.attendees.add(instance.member)
                        first_shift.save()
                    instance.term=get_current_term()
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
                    
            request.session['success_message']='Event and progress updated successfully'
            return redirect('event_cal:event_detail',event_id)
        else:
            request.session['error_message']='There were errors in your submission. Progress was not updated. Please correct the errors and try again.'
    else:
        formset = form_type(prefix='update_event',queryset=ProgressItem.objects.filter(related_event=e))
    template = loader.get_template('event_cal/update_event.html')
    context_dict = {
        'formset':formset,
        'event':e,
        'prefix':form_prefix,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
## change it so that the form has an extra column that is whether or not they signed in
# include the attendees as options as well
def complete_event(request, event_id):
    e = get_object_or_404(CalendarEvent,id=event_id)
    if not can_edit_event(request.user,e):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if not can_complete_event(e):
        request.session['error_message'] = 'This event can\'t be completed yet.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.is_fixed_progress():
        form_type = modelformset_factory(ProgressItem,exclude=('term','event_type','date_completed','amount_completed','related_event','name'),can_delete=True)
        is_fixed = True
    else:
        form_type = modelformset_factory(ProgressItem,exclude=('term','event_type','date_completed','related_event','name',),can_delete=True)
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
                instance.term=get_current_term()
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
                    shift.attendees.remove(attendee)
                shift.save()
            e.completed=True
            e.save()
            if duplicate_progress:
                request.session['warning_message']='The following members had progress listed twice, with latter listings ignored: '+ ','.join([prof.uniqname for prof in duplicate_progress])+'. Go to update progress to check that the amount of progress is correct'
            request.session['success_message']='Event and progress updated successfully'
            request.session['project_report_event']=event_id
            return redirect('event_cal:project_report')
        else:
            request.session['error_message']='There were errors in your submission. Progress was not updated. Please correct the errors and try again.'
    else:
        # create initial
        user_hours ={}
        for shift in e.eventshift_set.all():
            hours = (shift.end_time-shift.start_time).seconds/3600.0
            for attendee in shift.attendees.all():
                if not attendee.is_member():
                    continue
                if ProgressItem.objects.filter(related_event=e,member=attendee.memberprofile).exists():
                    continue
                if attendee in user_hours.keys():
                    user_hours[attendee.memberprofile]+=hours
                else:
                    user_hours[attendee.memberprofile]=hours
        initial = []                    
        for attendee in user_hours.keys():
            if is_fixed:
                initial.append({'member':attendee})
            else:
                initial.append({'member':attendee,'hours':user_hours[attendee]})
        form_type.extra=len(initial)+1
        formset = form_type(prefix=form_prefix,queryset=ProgressItem.objects.none(),initial=initial)
    template = loader.get_template('event_cal/complete_event.html')
    context_dict = {
        'formset':formset,
        'event':e,
        'prefix':form_prefix,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def complete_event_old(request, event_id):
    e = get_object_or_404(CalendarEvent,id=event_id)
    error_message= None
    if not can_edit_event(request.user,e):
        request.session['error_message']='You are not authorized to edit this event'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if e.is_fixed_progress():
        form_type = CompleteFixedProgressEventFormSet
        is_fixed = True
    else:
        form_type = CompleteEventFormSet
        is_fixed = False
    if not can_complete_event(e):
        request.session['error_message'] = 'You cannot complete this event. It is either already completed, or there are shifts in the future.'
        return get_previous_page(request,alternate='event_cal:event_detail',args=(event_id,))
    if request.method == 'POST':
        formset = form_type(request.POST,prefix='complete_event')
        if formset.is_valid():
            first_shift=e.eventshift_set.all()[0]
            for form in formset:
                if not 'attendee' in form.cleaned_data.keys():
                    continue
                attendee = form.cleaned_data['attendee']
                if 'DELETE' in form.cleaned_data.keys() and form.cleaned_data['DELETE']:
                    for shift in e.eventshift_set.all():
                        if attendee in shift.attendees.all():
                            shift.attendees.remove(attendee)
                            shift.save()
                    continue
                if not attendee.is_member():
                    continue
                if is_fixed:
                    hours = 1;
                else:
                    hours = form.cleaned_data['hours']
                p=ProgressItem(member=attendee.memberprofile,term=get_current_term(),event_type=e.event_type,amount_completed=hours,date_completed=date.today())
                p.name = e.name
                p.related_event=e
                p.save()
                if not e.eventshift_set.filter(attendees=attendee).exists():
                    first_shift.attendees.add(attendee)
                    first_shift.save()
            e.completed=True
            e.save()
            request.session['success_message']='Event completed and progress issued successfully'
            request.session['project_report_event']=event_id
            return redirect('event_cal:project_report')
        else:
            request.session['error_message']='There were errors in your submission. The event was not completed and progress was not issued. Please correct the errors and try again.'
    else:

        user_hours ={}
        for shift in e.eventshift_set.all():
            hours = (shift.end_time-shift.start_time).seconds/3600.0
            for attendee in shift.attendees.all():
                if attendee in user_hours.keys():
                    user_hours[attendee]+=hours
                else:
                    user_hours[attendee]=hours
        initial = []                    
        for attendee in user_hours.keys():
            if is_fixed:
                initial.append({'attendee':attendee})
            else:
                initial.append({'attendee':attendee,'hours':user_hours[attendee]})
        formset = form_type(initial=initial,prefix='complete_event')
    template = loader.get_template('event_cal/complete_event.html')
    context_dict = {
        'error':error_message,
        'formset':formset,
        'event':e,
        'prefix':'complete_event',
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
    now = timezone.localtime(timezone.now())
    announcement_parts = AnnouncementBlurb.objects.filter(start_date__lte=now.date).filter(end_date__gt=now.date)
    template = loader.get_template('event_cal/announcements.html')
    context_dict = {
        'announcement_parts':announcement_parts,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def add_announcement(request):
    if not Permissions.can_add_announcements(request.user):
        request.session['error_message']='You are not authorized to contribute weekly announcements.'
        return get_previous_page(request,alternate='event_cal:index')
    AnnouncementForm = modelform_factory(AnnouncementBlurb)
    AnnouncementForm.base_fields['contacts'].queryset=get_members().order_by('last_name') 
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
    template = loader.get_template('event_cal/add_announcement.html')
    context_dict = {
        'form':form,
        'dp_ids':dp_ids,
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
    return project_report(request)
def project_report_by_id(request,report_id):
    request.session.pop('project_report_event',None)
    request.session['project_report_id']=report_id
    return project_report(request)

def project_report(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create project reports.'
        return get_previous_page(request,alternate='event_cal:index')
    related_event = request.session.pop('project_report_event',None)
    report_id = request.session.pop('project_report_id',None)
    if related_event:
        event = CalendarEvent.objects.get(id=related_event)
        event_name=event.name
        if event.project_report:
            event_name=event.project_report.name
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
        elif report_id:
            form = ProjectReportForm(instance=report)
        else:
            form = ProjectReportForm()
    template = loader.get_template('event_cal/project_report.html')
    dp_ids=['id_planning_start_date']
    context_dict ={
            'form':form,
            'event':event_name,
            'dp_ids':dp_ids,
        }
    if related_event:
        request.session['project_report_event']=related_event
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
    current_chair = Officer.objects.filter(position__name='Campus Outreach Officer',term=get_current_term()).distinct()
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
            send_mail('We want your feedback on your recent tutoring session.',body,tutoring_email,[recipient_email],fail_silently=False)
            return get_previous_page(request,alternate='event_cal:index')          
        else:
            request.session['error_message']='There were errors in your submission, please correct them and resubmit. Your submission was not saved.'
    else:
        form = TutoringForm()
    dp_ids=['id_date_tutored']
    template = loader.get_template('event_cal/submit_tutoring_form.html')
    context_dict = {
        'form':form,
        'dp_ids':dp_ids,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))


def add_project_report_to_event(request,event_id):
    event=get_object_or_404(CalendarEvent,id=event_id)
    if not can_edit_event(request.user,event):
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
    template = loader.get_template('event_cal/attach_project_report.html')
    context_dict = {
        'form':form,
        'event':event,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
