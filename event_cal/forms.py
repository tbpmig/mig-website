from django import forms

from django.contrib.admin import widgets
from django.forms import ModelForm,Form,ValidationError
from django.forms.models import modelformset_factory,inlineformset_factory, BaseInlineFormSet,BaseFormSet
from django.forms.formsets import formset_factory
from django.utils.translation import ugettext as _

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget

from requirements.models import EventCategory
from event_cal.models import CalendarEvent, EventShift,AnnouncementBlurb
from mig_main.models import UserProfile,MemberProfile
from history.models import ProjectReport

class BaseAnnouncementForm(ModelForm):
    contacts = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Contact Person/People','closeOnSelect':True}), queryset=MemberProfile.get_members())

    class Meta:
        model = AnnouncementBlurb

class BaseEventForm(ModelForm):
    leaders = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Leader(s)','closeOnSelect':True}), queryset=MemberProfile.get_members())

    class Meta:
        model = CalendarEvent

class EventShiftForm(ModelForm):
    """
    Custom form for event shifts to verify that the event doesn't end before it starts and that mutually exclusive restrictions on attendance are not checked.
    """
    class meta:
        model = EventShift
    def clean(self):
        """
        Custom clean method that checks that the attendance restrictions are sane and that the start and end times are consistent.
        """
        cleaned_data = super(EventShiftForm,self).clean()
        ugrads_only = cleaned_data.get('ugrads_only')
        grads_only = cleaned_data.get('grads_only')
        electees_only = cleaned_data.get('electees_only')
        actives_only = cleaned_data.get('actives_only')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        if ugrads_only and grads_only:
            error_list.append(ValidationError(_('An event cannot be both \'only undergraduates\' and \'only graduates\'.')))
        if electees_only and actives_only:
            error_list.append(ValidationError(_('An event cannot be both \'only electees\' and \'only actives\'.')))
        if start_time> end_time:
            error_list.append(ValidationError(_('The event shift must start before it can end; use am/pm to specify.')))
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data

EventShiftFormset = inlineformset_factory(CalendarEvent, EventShift,form=EventShiftForm,exclude = ['drivers','attendees','google_event_id'],extra=1)

valid_time_formats=['%H:%M','%I:%M%p','%X','%I:%M %p','%I%p']
EventShiftFormset.form.base_fields['start_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftFormset.form.base_fields['start_time'].label='Select a start date and time'
EventShiftFormset.form.base_fields['end_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftFormset.form.base_fields['end_time'].label='Select an end date and time'

EventShiftEditFormset = inlineformset_factory(CalendarEvent, EventShift,form=EventShiftForm,extra=1,exclude=('google_event_id',))
EventShiftEditFormset.form.base_fields['start_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftEditFormset.form.base_fields['end_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftEditFormset.form.base_fields['start_time'].label='Select a start date and time'
EventShiftEditFormset.form.base_fields['end_time'].label='Select a end date and time'

class InterviewShiftForm(Form):
    """ Custom form for interviews. It captures only the necessary information to generate a sequence of event shifts based on the choices. The view logic can then make shifts for both interviewee and interviewer as needed.
    """
    date =forms.DateField()
    start_time = forms.TimeField(input_formats=valid_time_formats)
    end_time = forms.TimeField(input_formats=valid_time_formats)
    duration = forms.IntegerField(min_value=1,label='Interview Shift Length (min)')
    location = forms.CharField()
    grads_only = forms.BooleanField(required=False,label="Undergrads only (interviewer and interviewee)",initial=False)
    ugrads_only=  forms.BooleanField(required=False,label='Grads only (interviewer and interviewee)',initial=False)

    def clean(self):
        """
        Ensures that not both grads and undergrads -only options have been checked. Also makes sure start and end times make sense.
        """
        cleaned_data = super(InterviewShiftForm,self).clean()
        ugrads_only = cleaned_data.get('ugrads_only')
        grads_only = cleaned_data.get('grads_only')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        if ugrads_only and grads_only:
            error_list.append(ValidationError(_('An event cannot be both \'only undergraduates\' and \'only graduates\'.')))
        if start_time> end_time:
            error_list.append(ValidationError(_('The event shift must start before it can end; use am/pm to specify.')))
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data

class MultiShiftForm(Form):
    """
    Similar to the interview form, this is a custom form for creating multiple consecutive shifts for an event. It grabs the needed information to determine when all the shifts should take place.
    """
    date =forms.DateField()
    start_time = forms.TimeField(input_formats=valid_time_formats)
    end_time = forms.TimeField(input_formats=valid_time_formats)
    duration = forms.IntegerField(min_value=1,label='Shift Length (min)')
    location = forms.CharField()
    grads_only = forms.BooleanField(required=False,label="Undergrads only.",initial=False)
    ugrads_only=  forms.BooleanField(required=False,label='Grads only.',initial=False)

    electees_only = forms.BooleanField(required=False,label="Electees only.",initial=False)
    actives_only=  forms.BooleanField(required=False,label='Actives only.',initial=False)
    max_attendance = forms.IntegerField(min_value=0,label='Max attendance (per shift)',required=False)
    def clean(self):
        """
        Just like for interview creation and normal event shift creation, this vets that the attendance restrictions make sense and that the start time precedes the end time.
        """
        cleaned_data = super(MultiShiftForm,self).clean()
        ugrads_only = cleaned_data.get('ugrads_only')
        grads_only = cleaned_data.get('grads_only')
        electees_only = cleaned_data.get('electees_only')
        actives_only = cleaned_data.get('actives_only')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        if ugrads_only and grads_only:
            error_list.append(ValidationError(_('An event cannot be both \'only undergraduates\' and \'only graduates\'.')))
        if electees_only and actives_only:
            error_list.append(ValidationError(_('An event cannot be both \'only electees\' and \'only actives\'.')))
        if start_time> end_time:
            error_list.append(ValidationError(_('The event shift must start before it can end; use am/pm to specify.')))
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data
InterviewShiftFormset = formset_factory(InterviewShiftForm)
MultiShiftFormset = formset_factory(MultiShiftForm)



class CompleteEventForm(Form):
    """
    Form used to specify how many hours the attendee was at the event.
    """
    attendee = forms.ModelChoiceField(UserProfile.objects.all().order_by('last_name'),required=True)
    hours = forms.DecimalField(required=True)

CompleteEventFormSet = formset_factory(CompleteEventForm,can_delete=True)

class CompleteFixedProgressEventForm(Form):
    """
    For events where progress is fixed (i.e. you were there or you weren't) only listing attendees is necessary.
    """
    attendee = forms.ModelChoiceField(UserProfile.objects.all().order_by('last_name'))

CompleteFixedProgressEventFormSet = formset_factory(CompleteFixedProgressEventForm, can_delete=True)

class AddProjectReportForm(Form):
    """
    A form for selecting a project report to associate with a particular event.
    """
    report = forms.ModelChoiceField(ProjectReport.objects.all())

class MeetingSignInForm(Form):
    """
    Form for signing into events that use the event sign in feature. The name MeetingSignIn is because this used to be just used for meetings. 
    """
    secret_code = forms.CharField()
    quick_question = forms.CharField(widget=forms.Textarea)
    free_response = forms.CharField(widget=forms.Textarea,required=False)

    def __init__(self,*args, **kwargs):
        """
        Sets the question text for the quick question.
        """
        question = kwargs.pop('question_text',None)
        super(MeetingSignInForm,self).__init__(*args,**kwargs)
        if question:
            self.fields['quick_question'].label=question

class EventFilterForm(Form):
    """
    The form used to filter the events on the event list page. Queries preferences about the events to display.
    """
    after_date = forms.DateField(widget=forms.TextInput(attrs={'id':'dp_after'}),required=False)
    before_date = forms.DateField(widget=forms.TextInput(attrs={'id':'dp_before'}),required=False)
    event_reqs = forms.ModelMultipleChoiceField(queryset=EventCategory.objects.all(),widget=forms.CheckboxSelectMultiple,required=False)
    on_campus = forms.BooleanField(required=False)
    can_attend = forms.BooleanField(required=False,label='Events open to me')
