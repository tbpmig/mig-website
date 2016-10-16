from django import forms

from django.contrib.admin import widgets
from django.forms import ModelForm, Form, ValidationError
from django.forms.models import modelformset_factory, inlineformset_factory
from django.forms.models import BaseInlineFormSet, BaseFormSet
from django.forms.formsets import formset_factory
from django.utils.translation import ugettext as _


from django_select2.forms import Select2Widget, Select2MultipleWidget

from requirements.models import EventCategory, ProgressItem
from event_cal.models import CalendarEvent, EventShift
from event_cal.models import AnnouncementBlurb, EventPhoto
from mig_main.models import UserProfile, MemberProfile, AcademicTerm
from history.models import ProjectReport, MeetingMinutes


class BaseEventPhotoForm(ModelForm):
    """
    Form for adding photos. These can be associated with an event and/or a
    project report.
    """
    event = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=CalendarEvent.objects.all(),
                    required=False,
    )
    project_report = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=ProjectReport.objects.all(),
                    required=False
    )

    class Meta:
        model = EventPhoto
        fields = ['event', 'project_report', 'caption', 'photo']


class BaseEventPhotoFormAlt(ModelForm):
    """
    Form for adding photos. These can be associated with an event but not with
    a project report. The reason being that this form is used for users without
    sufficient permissions to create events and thus shouldn't be able to edit
    project reports.
    """
    event = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=CalendarEvent.objects.all(),
                    required=False,
    )

    class Meta:
        model = EventPhoto
        exclude = ('project_report',)


class BaseAnnouncementForm(ModelForm):
    """
    Form for creating and submitting announcements to be included in the weekly
    announcements sent to membership.
    """
    contacts = forms.ModelMultipleChoiceField(
                    widget=Select2MultipleWidget(),
                    queryset=MemberProfile.get_members()
    )

    class Meta:
        model = AnnouncementBlurb
        fields = [
            'start_date',
            'end_date',
            'title',
            'text',
            'contacts',
            'sign_up_link'
        ]


class BaseEventForm(ModelForm):
    """
    Form used in creating or editing event objects. This only creates the event
    itself, not the shifts, though the formset for creating those is often
    paired with this.
    """
    TWEET_CHOICES = (
        ('N', 'No Tweet'),
        ('T', 'Tweet normally'),
        ('H', 'Tweet with #UmichEngin'),
    )
    leaders = forms.ModelMultipleChoiceField(
                widget=Select2MultipleWidget(),
                queryset=MemberProfile.get_members()
    )
    tweet_option = forms.ChoiceField(
                    choices=TWEET_CHOICES,
                    initial='N'
    )
    agenda = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=MeetingMinutes.objects.filter(
                                semester=AcademicTerm.get_current_term(),
                                meeting_type__in=['NI','MM']
                ),
                required=False,
    )

    class Meta:
        model = CalendarEvent
        fields = [
                'name',
                'term',
                'event_type',
                'event_class',
                'description',
                'agenda',
                'google_cal',
                'leaders',
                'assoc_officer',
                'announce_start',
                'announce_text',
                'preferred_items',
                'min_unsign_up_notice',
                'min_sign_up_notice',
                'members_only',
                'needs_carpool',
                'use_sign_in',
                'allow_advance_sign_up',
                'needs_facebook_event',
                'needs_flyer',
                'requires_UM_background_check',
                'requires_AAPS_background_check',
                'mutually_exclusive_shifts',
                'allow_overlapping_sign_ups',
                'needs_COE_event',
        ]

    def clean(self):
        """
        Ensures that tweets are not sent or COE events not created for events
        which are marked as members-only
        """
        cleaned_data = super(BaseEventForm, self).clean()
        members_only = cleaned_data.get('members_only')
        tweet_option = cleaned_data.get('tweet_option')
        coe_option = cleaned_data.get('needs_COE_event')
        if members_only and not tweet_option == 'N':
            raise ValidationError(_('Tweeting is not currentlys supported'
                                    ' for members-only events'))
        if members_only and coe_option:
            raise ValidationError(_('Members-only events cannot be on the'
                                    ' COE Calendar.'))
        return cleaned_data


class EventShiftForm(ModelForm):
    """
    Custom form for event shifts to verify that the event doesn't end before
    it starts and that mutually exclusive restrictions on attendance are
    not checked.
    """

    class meta:
        model = EventShift

    def clean(self):
        """
        Custom clean method that checks that the attendance restrictions are
        sane and that the start and end times are consistent.
        """
        cleaned_data = super(EventShiftForm, self).clean()
        ugrads_only = cleaned_data.get('ugrads_only')
        grads_only = cleaned_data.get('grads_only')
        electees_only = cleaned_data.get('electees_only')
        actives_only = cleaned_data.get('actives_only')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        if ugrads_only and grads_only:
            error_list.append(
                        ValidationError(_('An event cannot be both '
                                          '\'only undergraduates\' and '
                                          '\'only graduates\'.'))
            )
        if electees_only and actives_only:
            error_list.append(
                        ValidationError(_('An event cannot be both '
                                          '\'only electees\' and \'only '
                                          'actives\'.'))
            )
        if not start_time or not end_time or start_time > end_time:
            error_list.append(
                        ValidationError(_('The event shift must start before '
                                          'it can end; use am/pm to specify.'))
            )
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data

EventShiftFormset = inlineformset_factory(
                                CalendarEvent,
                                EventShift,
                                form=EventShiftForm,
                                exclude=[
                                        'drivers',
                                        'attendees',
                                        'google_event_id'
                                ],
                                extra=1
)

valid_time_formats = ['%H:%M', '%I:%M%p', '%X', '%I:%M %p', '%I%p']
EventShiftFormset.form.base_fields['start_time'] = forms.SplitDateTimeField(
        input_time_formats=valid_time_formats
)
EventShiftFormset.form.base_fields['start_time'].label = ('Select a start '
                                                          'date and time')
EventShiftFormset.form.base_fields['end_time'] = forms.SplitDateTimeField(
        input_time_formats=valid_time_formats
)
EventShiftFormset.form.base_fields['end_time'].label = ('Select an end date '
                                                        'and time')

EventShiftEditFormset = inlineformset_factory(
                        CalendarEvent,
                        EventShift,
                        form=EventShiftForm,
                        extra=1,
                        exclude=['drivers', 'attendees', 'google_event_id']
)
EventShiftEditFormset.form.base_fields['start_time'] =\
    forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftEditFormset.form.base_fields['end_time'] = forms.SplitDateTimeField(
    input_time_formats=valid_time_formats
)
EventShiftEditFormset.form.base_fields['start_time'].label = ('Select a start '
                                                              'date and time')
EventShiftEditFormset.form.base_fields['end_time'].label = ('Select a end '
                                                            'date and time')


class InterviewShiftForm(Form):
    """ Custom form for interviews. It captures only the necessary information
    to generate a sequence of event shifts based on the choices. The view logic
    can then make shifts for both interviewee and interviewer as needed.
    """
    date = forms.DateField()
    start_time = forms.TimeField(input_formats=valid_time_formats)
    end_time = forms.TimeField(input_formats=valid_time_formats)
    duration = forms.IntegerField(
                                min_value=1,
                                label='Interview Shift Length (min)'
    )
    locations = forms.CharField(label='Comma-separated list of room locations')
    number_of_parts = forms.IntegerField(min_value=1, max_value=2)
    type_choices = (
        ('N', 'Normal: Any electee, any active'),
        ('U', 'Undergrads only (interviewer and interviewee)'),
        ('G', 'Grads only (interviewer and interviewee)'),
        ('UI', 'Undergrad interviewee, any active interviewer'),
        ('GI', 'Grad interviewee, any active interviewer'),
        )
    interview_type = forms.ChoiceField(choices=type_choices, initial='N')

    def clean(self):
        """
        Ensures that not both grads and undergrads -only options have been
        checked. Also makes sure start and end times make sense.
        """
        cleaned_data = super(InterviewShiftForm, self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        if not start_time or not end_time or start_time > end_time:
            error_list.append(ValidationError(_('The event shift must start '
                                                'before it can end; use am/pm '
                                                'to specify.')))
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data


class MultiShiftForm(Form):
    """
    Similar to the interview form, this is a custom form for creating multiple
    consecutive shifts for an event. It grabs the needed information to
    determine when all the shifts should take place.
    """
    date = forms.DateField()
    start_time = forms.TimeField(input_formats=valid_time_formats)
    end_time = forms.TimeField(input_formats=valid_time_formats)
    duration = forms.IntegerField(min_value=1, label='Shift Length (min)')
    location = forms.CharField()
    ugrads_only = forms.BooleanField(
                        required=False,
                        label="Undergrads only.",
                        initial=False
    )
    grads_only = forms.BooleanField(
                        required=False,
                        label='Grads only.',
                        initial=False
    )

    electees_only = forms.BooleanField(
                        required=False,
                        label="Electees only.",
                        initial=False
    )
    actives_only = forms.BooleanField(
                        required=False,
                        label='Actives only.',
                        initial=False
    )
    max_attendance = forms.IntegerField(
                        min_value=0,
                        label='Max attendance (per shift)',
                        required=False
    )

    def clean(self):
        """
        Just like for interview creation and normal event shift creation,
        this vets that the attendance restrictions make sense and that the
        start time precedes the end time.
        """
        cleaned_data = super(MultiShiftForm, self).clean()
        ugrads_only = cleaned_data.get('ugrads_only')
        grads_only = cleaned_data.get('grads_only')
        electees_only = cleaned_data.get('electees_only')
        actives_only = cleaned_data.get('actives_only')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        error_list = []
        if ugrads_only and grads_only:
            error_list.append(
                        ValidationError(_('An event cannot be both \'only '
                                          'undergraduates\' and \'only '
                                          'graduates\'.'))
            )
        if electees_only and actives_only:
            error_list.append(
                        ValidationError(_('An event cannot be both \'only '
                                          'electees\' and \'only actives\'.'))
            )
        if start_time and end_time:
            if start_time > end_time:
                error_list.append(
                        ValidationError(_('The event shift must start before '
                                          'it can end; use am/pm to specify.'))
                )
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data


InterviewShiftFormset = formset_factory(InterviewShiftForm)
MultiShiftFormset = formset_factory(MultiShiftForm)


class CompleteEventForm(ModelForm):
    """
    Form used to specify how many hours the attendee was at the event.
    """
    member = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=MemberProfile.get_members()
    )

    class Meta:
        model = ProgressItem
        exclude = (
                'term',
                'event_type',
                'date_completed',
                'related_event',
                'name'
        )


CompleteEventFormSet = modelformset_factory(
                        ProgressItem,
                        form=CompleteEventForm,
                        can_delete=True
)


class CompleteFixedProgressEventForm(ModelForm):
    """
    For events where progress is fixed (i.e. you were there or you weren't)
    only listing attendees is necessary.
    """
    member = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=MemberProfile.get_members()
    )

    class Meta:
        model = ProgressItem
        exclude = (
                'term',
                'event_type',
                'date_completed',
                'amount_completed',
                'related_event',
                'name',
                'hours',
        )


CompleteFixedProgressEventFormSet = modelformset_factory(
                                    ProgressItem,
                                    form=CompleteFixedProgressEventForm,
                                    can_delete=True
)


class AddProjectReportForm(Form):
    """
    A form for selecting a project report to associate with a particular event.
    """
    report = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=ProjectReport.objects.all()
    )


class MeetingSignInForm(Form):
    """
    Form for signing into events that use the event sign in feature. The name
    MeetingSignIn is because this used to be just used for meetings.
    """
    secret_code = forms.CharField()
    quick_question = forms.CharField(widget=forms.Textarea)
    free_response = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        """
        Sets the question text for the quick question.
        """
        question = kwargs.pop('question_text', None)
        super(MeetingSignInForm, self).__init__(*args, **kwargs)
        if question:
            self.fields['quick_question'].label = question


class EventFilterForm(Form):
    """
    The form used to filter the events on the event list page. Queries
    preferences about the events to display.
    """
    after_date = forms.DateField(
                widget=forms.TextInput(
                            attrs={'id': 'dp_after'}
                ),
                required=False
    )
    before_date = forms.DateField(
                widget=forms.TextInput(
                            attrs={'id': 'dp_before'}
                ),
                required=False
    )
    event_reqs = forms.ModelMultipleChoiceField(
                    queryset=EventCategory.objects.all(),
                    widget=forms.CheckboxSelectMultiple,
                    required=False
    )
    on_campus = forms.BooleanField(required=False)
    can_attend = forms.BooleanField(required=False, label='Events open to me')


class EventEmailForm(Form):
    """
    The form used to get the subject and email body for emailing event
    participants.
    """
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)
