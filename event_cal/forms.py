from django import forms

from django.contrib.admin import widgets
from django.forms import ModelForm,Form,ValidationError
from django.forms.models import modelformset_factory,inlineformset_factory, BaseInlineFormSet,BaseFormSet
from django.forms.formsets import formset_factory
from django.utils.translation import ugettext as _

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from requirements.models import EventCategory,ProgressItem
from event_cal.models import CalendarEvent, EventShift,AnnouncementBlurb,EventPhoto
from mig_main.models import UserProfile,MemberProfile
from history.models import ProjectReport
class BaseEventPhotoForm(ModelForm):
    event = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Event','closeOnSelect':True}),queryset=CalendarEvent.objects.all(),required=False)
    project_report = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Report','closeOnSelect':True}),queryset=ProjectReport.objects.all(),required=False)
    class Meta:
        model = EventPhoto
        fields = ['event','project_report','caption','photo']
class BaseEventPhotoFormAlt(ModelForm):
    event = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Event','closeOnSelect':True}),queryset=CalendarEvent.objects.all(),required=False)
    class Meta:
        model = EventPhoto
        exclude = ('project_report',)

class BaseAnnouncementForm(ModelForm):
    contacts = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Contact Person/People','closeOnSelect':True}), queryset=MemberProfile.get_members())

    class Meta:
        model = AnnouncementBlurb
        fields=['start_date','end_date','title','text','contacts','sign_up_link']

class BaseEventForm(ModelForm):
    TWEET_CHOICES= (
        ('N','No Tweet'),
        ('T','Tweet normally'),
        ('H','Tweet with #UmichEngin'),
    )
    leaders = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Leader(s)','closeOnSelect':True}), queryset=MemberProfile.get_members())
    tweet_option = forms.ChoiceField(choices=TWEET_CHOICES,initial='N')
    class Meta:
        model = CalendarEvent
        exclude=('completed','google_event_id','project_report')
    def clean(self):
        cleaned_data = super(BaseEventForm,self).clean()
        members_only = cleaned_data.get('members_only')
        tweet_option = cleaned_data.get('tweet_option')
        if members_only and not tweet_option=='N':
            raise ValidationError(_('Tweeting is not currentlys supported for members-only events'))
        return cleaned_data
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
        if not start_time or not end_time or start_time> end_time:
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

EventShiftEditFormset = inlineformset_factory(CalendarEvent, EventShift,form=EventShiftForm,extra=1,exclude=['drivers','attendees','google_event_id'])
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
    type_choices = (
        ('N','Normal: Any electee, any active'),
        ('U','Undergrads only (interviewer and interviewee)'),
        ('G','Grads only (interviewer and interviewee)'),
        ('UI','Undergrad interviewee, any active interviewer'),
        ('GI','Grad interviewee, any active interviewer'),
        )
    interview_type = forms.ChoiceField(choices=type_choices)
    def clean(self):
        """
        Ensures that not both grads and undergrads -only options have been checked. Also makes sure start and end times make sense.
        """
        cleaned_data = super(InterviewShiftForm,self).clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        error_list = []
        
        if not start_time or not end_time or start_time> end_time:
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



class CompleteEventForm(ModelForm):
    """
    Form used to specify how many hours the attendee was at the event.
    """
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Attendee','closeOnSelect':True}),queryset=MemberProfile.get_members())
    class Meta:
        model = ProgressItem
        exclude = ('term','event_type','date_completed','related_event','name')

CompleteEventFormSet = modelformset_factory(ProgressItem, form=CompleteEventForm,can_delete=True)

class CompleteFixedProgressEventForm(ModelForm):
    """
    For events where progress is fixed (i.e. you were there or you weren't) only listing attendees is necessary.
    """
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'26em','placeholder':'Select Attendee','closeOnSelect':True}),queryset=MemberProfile.get_members())
    class Meta:
        model = ProgressItem
        exclude = ('term','event_type','date_completed','amount_completed','related_event','name','hours',)    
CompleteFixedProgressEventFormSet = modelformset_factory(ProgressItem,form=CompleteFixedProgressEventForm, can_delete=True)

class AddProjectReportForm(Form):
    """
    A form for selecting a project report to associate with a particular event.
    """
    report = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Report','closeOnSelect':True}), queryset=ProjectReport.objects.all())

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

class EventEmailForm(Form):
    """
    The form used to get the subject and email body for emailing event participants.
    """
    subject = forms.CharField()
    body = forms.CharField(widget=forms.Textarea)
