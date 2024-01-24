from django.core.urlresolvers import reverse
from django.db.models import Min
from django.http import HttpResponse
from django.forms.models import modelformset_factory
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.utils import timezone

from event_cal.models import CalendarEvent
from history.models import Officer
from mig_main import messages
from mig_main.models import OfficerPosition, AcademicTerm, MemberProfile
from mig_main.utility import get_message_dict, get_previous_page, Permissions
from outreach.models import (
                    OutreachPhoto,
                    MindSETModule,
                    VolunteerFile,
                    TutoringPageSection,
                    OutreachEventType,
                    MindSETProfileAdditions,
                    OutreachEvent,
)


def get_permissions(user):
    permission_dict = {
        'can_edit_mindset': Permissions.can_update_mindset_materials(user),
        'can_edit_outreach': user.is_superuser,
        'can_edit_profiles': Permissions.can_manage_officers(user),
    }
    return permission_dict


def get_common_context(request):
    context_dict = get_message_dict(request)
    user_is_member = False
    has_profile = False
    event_signed_up = request.session.pop('event_signed_up', None)
    if hasattr(request.user, 'userprofile'):
        has_profile = True
        if request.user.userprofile.is_member():
            user_is_member = True
    context_dict.update({
        'request': request,
        'term': AcademicTerm.get_current_term(),
        'user_is_member': user_is_member,
        'has_profile': has_profile,
        'event_signed_up': event_signed_up,
        'now': timezone.now(),
        'main_nav': 'outreach',
    })
    return context_dict


def index(request):
    request.session['current_page'] = request.path
    template = loader.get_template('outreach/outreach.html')
    context_dict = {
        'subnav': 'index',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


def mindset(request):
    request.session['current_page'] = request.path
    template = loader.get_template('outreach/MindSET.html')
    k_12_officers = Officer.objects.filter(
                position__name='K-12 Outreach Officer'
    ).order_by('-term__year', 'term__semester_type__name')
    officers_unique = []
    id_set = set()
    term = AcademicTerm.get_current_term()
    positions = OfficerPosition.objects.filter(name='K-12 Outreach Officer')
    current_officers = k_12_officers.filter(term=term)

    if positions.exists:
        position = positions[0]
    else:
        position = None
    for officer in k_12_officers:
        if officer.user.uniqname in id_set:
            continue
        else:
            id_set |= set([officer.user.uniqname])
            officers = current_officers.filter(
                                    user__uniqname=officer.user.uniqname
            )
            if not officers.exists():
                officers_unique.append(officer)

    mindset_main_photo = OutreachPhoto.objects.filter(
                                photo_type__name='MindSET_Main'
    )
    mindset_slideshow_photos = OutreachPhoto.objects.filter(
                                photo_type__name='MindSET_Slideshow',
                                active=True
    )
    if mindset_main_photo.exists():
        main_photo = mindset_main_photo[0]
    else:
        main_photo = None
    mindset_parking_photo = OutreachPhoto.objects.filter(
                                photo_type__name='MindSET_Map'
    )
    if mindset_parking_photo.exists():
        parking_photo = mindset_parking_photo[0]
    else:
        parking_photo = None
    events = CalendarEvent.objects.filter(
                term=term,
                event_type__name='MindSET'
    ).annotate(
            earliest_shift=Min('eventshift__start_time')
    ).order_by(
            'earliest_shift'
    )
    context_dict = {
            'events': events,
            'main_photo': main_photo,
            'parking_photo': parking_photo,
            'modules': MindSETModule.objects.all(),
            'k_12_officers': officers_unique,
            'position': position,
            'current_officers': current_officers,
            'volunteer_files': VolunteerFile.objects.all(),
            'slideshow_photos': mindset_slideshow_photos,
            'subnav': 'mindset',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


def update_mindset_modules(request):
    if not Permissions.can_update_mindset_materials(request.user):
        request.session['error_message'] = ('You are not authorized to '
                                            'update MindSET Materials')
        return redirect('outreach:mindset')
    MindSETModuleForm = modelformset_factory(MindSETModule, can_delete=True, exclude=[])
    formset = MindSETModuleForm(
                    request.POST or None,
                    request.FILES or None,
                    prefix='mindset'
    )
    if request.method == 'POST':
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message'] = 'Modules updated.'
            return redirect('outreach:mindset')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'formset': formset,
        'prefix': 'mindset',
        'subnav': 'mindset',
        'has_files': True,
        'submit_name': 'Update Modules',
        'back_button': {
                    'link': reverse('outreach:mindset'),
                    'text': 'To MindSET Page'
        },
        'form_title': 'Edit MindSET Module Resources',
        'help_text': ('Keep track of the resources associated with MindSET '
                      'modules here.'),
        'can_add_row': True,
        'base': 'outreach/base_outreach.html',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context_dict, request))


def update_mindset_profile_additions(request):
    if not Permissions.can_manage_officers(request.user):
        request.session['error_message'] = ('You are not authorized to update '
                                            'MindSET Profile additions')
        return redirect('outreach:mindset')
    MindSETProfileForm = modelformset_factory(
                            MindSETProfileAdditions,
                            can_delete=True,
                            exclude=[]
    )
    MindSETProfileForm.form.base_fields['user'].queryset = \
        MemberProfile.objects.filter(
                officer__in=Officer.objects.filter(
                        position__name='K-12 Outreach Officer'
                )
        ).distinct()
    prefix = 'mindset_profile'
    formset = MindSETProfileForm(request.POST or None, prefix=prefix)
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = ('Profile additions '
                                                  'successfully updated.')
            return redirect('outreach:mindset')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'formset': formset,
        'prefix': prefix,
        'subnav': 'mindset',
        'has_files': False,
        'submit_name': 'Update MindSET Profile Additions',
        'back_button': {
                'link': reverse('outreach:mindset'),
                'text': 'To MindSET Page'
        },
        'form_title': 'Edit MindSET Profile Additions',
        'help_text': 'Add fun facts and the like for K-12 Outreach Officers.',
        'can_add_row': True,
        'base': 'outreach/base_outreach.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context_dict, request))


def update_mindset_photos(request):
    if not Permissions.can_update_mindset_materials(request.user):
        request.session['error_message'] = ('You are not authorized to update '
                                            'MindSET Materials')
        return redirect('outreach:mindset')
    MindSETPhotoForm = modelformset_factory(OutreachPhoto, can_delete=True, exclude=[])
    formset = MindSETPhotoForm(
                    request.POST or None,
                    request.FILES or None,
                    prefix='mindset'
    )
    if request.method == 'POST':
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message'] = 'Photos successfully updated.'
            return redirect('outreach:mindset')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'formset': formset,
        'prefix': 'mindset',
        'subnav': 'mindset',
        'has_files': True,
        'submit_name': 'Update MindSET Photos',
        'back_button': {
                'link': reverse('outreach:mindset'),
                'text': 'To MindSET Page'
        },
        'form_title': 'Edit MindSET Photos',
        'help_text': ('You can update the photos for the MindSET section of '
                      'the website here.'),
        'can_add_row': True,
        'base': 'outreach/base_outreach.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context_dict, request))


def tutoring(request):
    request.session['current_page'] = request.path
    events = CalendarEvent.objects.filter(
                term=AcademicTerm.get_current_term(),
                event_type__name='Tutoring Hours').order_by('announce_start')
    officers = Officer.objects.filter(position__name='Campus Outreach Officer')
    template = loader.get_template('outreach/tutoring.html')
    tutoring_pages = TutoringPageSection.objects.all().order_by('page_order')
    context_dict = {
        'events': events,
        'tutoring_officers': officers,
        'pages': tutoring_pages,
        'subnav': 'tutoring',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


def outreach_event(request, url_stem):
    request.session['current_page'] = request.path
    outreach_event = get_object_or_404(OutreachEventType, url_stem=url_stem)
    relevant_officers = Officer.objects.filter(
                    user__uniqname=request.user.username,
                    term=AcademicTerm.get_current_term(),
                    position__in=outreach_event.officers_can_edit.all()
    )
    events = CalendarEvent.objects.filter(
                    term=AcademicTerm.get_current_term(),
                    event_type=outreach_event.event_category,
                    eventshift__end_time__gte=timezone.now()
    ).annotate(
        earliest_shift=Min('eventshift__start_time')
    ).order_by('earliest_shift')
    template = loader.get_template('outreach/outreach_template.html')
    context_dict = {
        'events': events,
        'subnav': url_stem,
        'title': outreach_event.title,
        'text': outreach_event.text,
        'has_cal_events': outreach_event.has_calendar_events,
        'event_category': outreach_event.event_category.name,
        'can_edit_outreach_event': (request.user.is_superuser or
                                    relevant_officers.exists()),
        'event_timeline': outreach_event.outreachevent_set.all().order_by(
                                                    '-pin_to_top',
                                                    '-id'
        ),
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


def hide_outreach_event(request, url_stem):
    if not request.user.is_superuser:
        request.session['error_message'] = ('You are not authorized to edit '
                                            'outreach events')
        return get_previous_page(request, alternate='outreach:index')
    outreach_event = get_object_or_404(OutreachEventType, url_stem=url_stem)
    outreach_event.visible = False
    outreach_event.save()
    return redirect('outreach:index')


def manage_outreach_event_types(request):
    if not request.user.is_superuser:
        request.session['error_message'] = ('You are not authorized to edit '
                                            'outreach events types')
        return get_previous_page(request, alternate='outreach:index')
    OutreachFormSet = modelformset_factory(OutreachEventType, exclude=[])
    prefix = 'outreach'
    formset = OutreachFormSet(request.POST or None, prefix=prefix)
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = ('Outraech event types '
                                                  'successfully updated.')
            return redirect('outreach:mindset')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'formset': formset,
        'prefix': prefix,
        'subnav': 'index',
        'has_files': False,
        'submit_name': 'Update Outreach Event Types',
        'back_button': {
                    'link': reverse('outreach:index'),
                    'text': 'To Outreach Page'
        },
        'form_title': 'Edit Outreach Events and Types',
        'help_text': ('Update or add new outreach event categories to '
                      'display in the outreach section. Make sure to add '
                      'the corresponding event category from the membership '
                      'section first if needed.'),
        'can_add_row': True,
        'base': 'outreach/base_outreach.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context_dict, request))


def manage_outreach_events(request, url_stem):
    outreach_event = get_object_or_404(OutreachEventType, url_stem=url_stem)
    relevant_officers = Officer.objects.filter(
                        user__uniqname=request.user.username,
                        term=AcademicTerm.get_current_term(),
                        position__in=outreach_event.officers_can_edit.all()
    )
    if not (request.user.is_superuser or relevant_officers.exists()):
        request.session['error_message'] = ('You are not authorized to edit '
                                            'outreach events')
        return get_previous_page(request, alternate='outreach:index')
    OutreachFormSet = modelformset_factory(
                            OutreachEvent,
                            exclude=['outreach_event']
    )
    prefix = 'outreach'
    formset = OutreachFormSet(
                    request.POST or None,
                    request.FILES or None,
                    prefix=prefix,
                    queryset=OutreachEvent.objects.filter(
                                outreach_event=outreach_event
                    )
    )

    if request.method == 'POST':
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.outreach_event = outreach_event
                instance.save()
            request.session['success_message'] = ('Outraech Events '
                                                  'successfully updated.')
            return redirect('outreach:mindset')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'formset': formset,
        'prefix': prefix,
        'subnav': 'index',
        'has_files': True,
        'submit_name': 'Update Outreach Events',
        'back_button': {
                    'link': reverse('outreach:outreach_event',
                                    args=[url_stem]),
                    'text': 'To %s Page' % (outreach_event.title)
        },
        'form_title': 'Edit %s Events' % (outreach_event.title),
        'help_text': ('Update or add new outreach events to display in '
                      'the %s section.') % (outreach_event.title),
        'can_add_row': True,
        'base': 'outreach/base_outreach.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context_dict, request))
