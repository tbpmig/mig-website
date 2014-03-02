from django import forms
from django.forms import ModelForm,Form,ValidationError
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.forms.formsets import formset_factory#BaseInlineFormSet
from django.contrib.admin import widgets
from requirements.models import EventCategory
from event_cal.models import CalendarEvent, EventShift
from mig_main.models import UserProfile
from history.models import ProjectReport

class EventForm(ModelForm):
    class Meta:
        model = CalendarEvent
        exclude = ['completed','google_event_id']
class BaseEventShiftFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        for form in self.forms:
            if  'start_time'in form.cleaned_data and 'end_time' in form.cleaned_data:
                if form.cleaned_data['start_time']>form.cleaned_data['end_time']:
                    raise ValidationError("The event must start before it can end; use am/pm to specify.")

EventShiftFormset = inlineformset_factory(CalendarEvent, EventShift,formset=BaseEventShiftFormSet,exclude = ['drivers','attendees','google_event_id'],extra=1)

valid_time_formats=['%H:%M','%I:%M%p','%X','%I:%M %p','%I%p']
EventShiftFormset.form.base_fields['start_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftFormset.form.base_fields['start_time'].label='Select a start date and time'
EventShiftFormset.form.base_fields['end_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftFormset.form.base_fields['end_time'].label='Select an end date and time'

EventShiftEditFormset = inlineformset_factory(CalendarEvent, EventShift,formset=BaseEventShiftFormSet,extra=1,exclude=('google_event_id',))
EventShiftEditFormset.form.base_fields['start_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftEditFormset.form.base_fields['end_time']=forms.SplitDateTimeField(input_time_formats=valid_time_formats)
EventShiftEditFormset.form.base_fields['start_time'].label='Select a start date and time'
EventShiftEditFormset.form.base_fields['end_time'].label='Select a end date and time'
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
