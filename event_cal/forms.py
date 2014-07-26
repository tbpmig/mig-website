from django import forms

from django.contrib.admin import widgets
from django.forms import ModelForm,Form,ValidationError
from django.forms.models import modelformset_factory,inlineformset_factory, BaseInlineFormSet,BaseFormSet
from django.forms.formsets import formset_factory
from django.utils.translation import ugettext as _

from requirements.models import EventCategory
from event_cal.models import CalendarEvent, EventShift
from mig_main.models import UserProfile
from history.models import ProjectReport

class EventForm(ModelForm):
    class Meta:
        model = CalendarEvent
        exclude = ['completed','google_event_id']

class EventShiftForm(ModelForm):
    class meta:
        model = EventShift
        #exclude = ['drivers','attendees','google_event_id']
        #extra=1
    def clean(self):
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

#class BaseEventShiftFormSet(BaseInlineFormSet):
#    def clean(self):
#        if any(self.errors):
#            return
#        for form in self.forms:
#            if form.cleaned_data['grads_only'] and form.cleaned_data['ugrads_only']:
#            if form.cleaned_data['electees_only'] and form.cleaned_data['actives_only']:
#                raise ValidationError(_('An event cannot be both \'only electeess\' and \'only actives\'.'))
#            if  'start_time'in form.cleaned_data and 'end_time' in form.cleaned_data:
#                if form.cleaned_data['start_time']>form.cleaned_data['end_time']:
#                    raise ValidationError("The event must start before it can end; use am/pm to specify.")

#EventShiftFormset = inlineformset_factory(CalendarEvent, EventShift,formset=BaseEventShiftFormSet,exclude = ['drivers','attendees','google_event_id'],extra=1)
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
    date =forms.DateField()
    start_time = forms.TimeField(input_formats=valid_time_formats)
    end_time = forms.TimeField(input_formats=valid_time_formats)
    duration = forms.IntegerField(min_value=1,label='Interview Shift Length (min)')
    location = forms.CharField()
    grads_only = forms.BooleanField(required=False,label="Undergrads only (interviewer and interviewee)",initial=False)
    ugrads_only=  forms.BooleanField(required=False,label='Grads only (interviewer and interviewee)',initial=False)

    def clean(self):
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
    attendee = forms.ModelChoiceField(UserProfile.objects.all().order_by('last_name'),required=True)
    hours = forms.DecimalField(required=True)

CompleteEventFormSet = formset_factory(CompleteEventForm,can_delete=True)

class CompleteFixedProgressEventForm(Form):
    attendee = forms.ModelChoiceField(UserProfile.objects.all().order_by('last_name'))

CompleteFixedProgressEventFormSet = formset_factory(CompleteFixedProgressEventForm, can_delete=True)

class AddProjectReportForm(Form):
    report = forms.ModelChoiceField(ProjectReport.objects.all())

class MeetingSignInForm(Form):
    secret_code = forms.CharField()
    quick_question = forms.CharField(widget=forms.Textarea)
    free_response = forms.CharField(widget=forms.Textarea,required=False)

    def __init__(self,*args, **kwargs):
        question = kwargs.pop('question_text',None)
        super(MeetingSignInForm,self).__init__(*args,**kwargs)
        if question:
            self.fields['quick_question'].label=question

class EventFilterForm(Form):
    after_date = forms.DateField(widget=forms.TextInput(attrs={'id':'dp_after'}),required=False)
    before_date = forms.DateField(widget=forms.TextInput(attrs={'id':'dp_before'}),required=False)
    event_reqs = forms.ModelMultipleChoiceField(queryset=EventCategory.objects.all(),widget=forms.CheckboxSelectMultiple,required=False)
    on_campus = forms.BooleanField(required=False)
    can_attend = forms.BooleanField(required=False,label='Events I open to me')
