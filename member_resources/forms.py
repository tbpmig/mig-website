from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory
from django.db.models import Q

from mig_main.models import MemberProfile, UserProfile,UserPreference,PREFERENCES,get_members,get_actives
from history.models import MeetingMinutes, Officer
from requirements.models import Requirement,EventCategory,ProgressItem
def max_peer_interviews_validator(value):
    requirement = Requirement.objects.filter(event_category__name='Peer Interviews')
    if requirement:
        if value>requirement[0].amount_required:
            raise ValidationError(u'This value cannot exceed %s' % requirement[0].amount_required)

def max_essays_validator(value):
    requirement = Requirement.objects.filter(event_category__name='Essays')
    if requirement:
        if value > requirement[0].amount_required:
            raise ValidationError(u'This value cannot exceed %s'%requirement[0].amount_required)

class MemberProfileForm(ModelForm):
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','init_chapter','UMID','init_term','still_electing','edu_bckgrd_form')

class ElecteeProfileForm(ModelForm):
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','init_chapter','UMID','init_term','still_electing','standing', 'alum_mail_freq','job_field','employer','meeting_speak','edu_bckgrd_form')

class MemberProfileNewActiveForm(ModelForm):
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','edu_bckgrd_form','still_electing')

class MemberProfileNewElecteeForm(ModelForm):
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','standing','init_chapter','alum_mail_freq','job_field','employer','meeting_speak','init_term','still_electing','edu_bckgrd_form')

class NonMemberProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user','uniqname')

class MeetingMinutesForm(ModelForm):
    class Meta:
        model = MeetingMinutes

class ManageElecteeStillElectingForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    still_electing = forms.BooleanField(required=False)

ManageElecteeStillElecting = formset_factory(ManageElecteeStillElectingForm,extra=0)
class ManageDuesForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    dues_paid = forms.BooleanField(required=False)

ManageDuesFormSet = formset_factory(ManageDuesForm,extra=0)

class ManageInterviewForm(Form):
    member=forms.ModelChoiceField(queryset=get_actives().order_by('last_name'))
    interview_type=forms.ModelChoiceField(queryset=EventCategory.objects.filter(parent_category__name='Conducted Interviews'))
    number_of_interviews = forms.IntegerField(min_value=0)
ManageInterviewsFormSet = formset_factory(ManageInterviewForm,extra=1)

class ManageUgradPaperWorkForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    electee_exam_completed = forms.BooleanField(required=False)
    peer_interviews_completed = forms.IntegerField(min_value=0,validators=[max_peer_interviews_validator])
    character_essays_completed = forms.IntegerField(min_value=0,validators=[max_essays_validator])
    interviews_completed = forms.BooleanField(required=False)
    group_meetings = forms.IntegerField(min_value=0)

ManageUgradPaperWorkFormSet = formset_factory(ManageUgradPaperWorkForm,extra=0)
    
class ManageActiveGroupMeetingsForm(Form):
    member=forms.ModelChoiceField(queryset=get_actives().filter(~Q(electee_group_leaders=None,electee_group_officers=None)).distinct().order_by('last_name'))
    group_meetings = forms.IntegerField(min_value=0)

ManageActiveGroupMeetingsFormSet = formset_factory(ManageActiveGroupMeetingsForm,extra=1)

class ManageGradPaperWorkForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    educational_background_form_completed = forms.BooleanField(required=False)
    advisor_form_completed = forms.BooleanField(required=False)
    interviews_completed = forms.BooleanField(required=False)
ManageGradPaperWorkFormSet = formset_factory(ManageGradPaperWorkForm,extra=0)

class ManageProjectLeaderForm(Form):
    member = forms.ModelChoiceField(queryset=get_members().order_by('last_name'))
    is_project_leader = forms.BooleanField(required=False)
ManageProjectLeadersFormSet = formset_factory(ManageProjectLeaderForm,extra=3)

ManageOfficersFormSet = modelformset_factory(Officer)

class MassAddProjectLeadersForm(Form):
    uniqnames = forms.CharField(widget=forms.Textarea)

class PreferenceForm(Form):
    def __init__(self,prefs,*args,**kwargs):
        super(PreferenceForm,self).__init__(*args,**kwargs)
        for pref in prefs:
            self.fields[pref['name']]=forms.ChoiceField(choices=[(pref['values'].index(d),d) for d in pref['values']])
            self.fields[pref['name']].label = pref['verbose']

class LeadershipCreditForm(forms.ModelForm):
    approve= forms.BooleanField(required=False)

    class Meta:
        model = ProgressItem
        exclude= ('term','event_type','amount_completed','date_completed','related_event')

    def save(self,commit=True):
        approved=self.cleaned_data.pop('approve',False)
        if approved:
            return super(LeadershipCreditForm, self).save(commit=commit)
        else:
            return None

LeadershipCreditFormSet = modelformset_factory(ProgressItem,form=LeadershipCreditForm)
