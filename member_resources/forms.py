from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory
from django.db.models import Q

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from electees.models import ElecteeGroup
from mig_main.models import AcademicTerm,Major,MemberProfile, TBPChapter,UserProfile,UserPreference,PREFERENCES,TBPraise
from history.models import MeetingMinutes, Officer,Distinction
from requirements.models import Requirement,EventCategory,ProgressItem,DistinctionType
def max_peer_interviews_validator(value):
    requirement = Requirement.objects.filter(event_category__name='Peer Interviews')
    if requirement:
        if value>requirement[0].amount_required:
            raise ValidationError(u'This value cannot exceed %s' % requirement[0].amount_required)

class MemberProfileForm(ModelForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','UMID','still_electing','edu_bckgrd_form')
        #exclude=('user','uniqname','status','init_chapter','UMID','init_term','still_electing','edu_bckgrd_form')

class ElecteeProfileForm(ModelForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','init_chapter','UMID','init_term','still_electing','standing', 'alum_mail_freq','job_field','employer','meeting_speak','edu_bckgrd_form')

class MemberProfileNewActiveForm(ModelForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    init_term = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'12em','placeholder':'Select Term','closeOnSelect':True}),queryset=AcademicTerm.get_rchron(),label='Initiation Term')
    init_chapter = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'10em','placeholder':'Select Chapter','closeOnSelect':True}),queryset=TBPChapter.objects.all(),label='Initiating Chapter')
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','edu_bckgrd_form','still_electing')

class MemberProfileNewElecteeForm(ModelForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    class Meta:
        model = MemberProfile
        exclude=('user','uniqname','status','standing','init_chapter','alum_mail_freq','job_field','employer','meeting_speak','init_term','still_electing','edu_bckgrd_form')

class NonMemberProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user','uniqname')

class MeetingMinutesForm(ModelForm):
    semester = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'10em','placeholder':'Select Term','closeOnSelect':True}),queryset=AcademicTerm.get_rchron(),initial=AcademicTerm.get_current_term())
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
    member=forms.ModelChoiceField(queryset=MemberProfile.get_actives().order_by('last_name'))
    interview_type=forms.ModelChoiceField(queryset=EventCategory.objects.filter(parent_category__name='Conducted Interviews'))
    number_of_interviews = forms.IntegerField(min_value=0)
ManageInterviewsFormSet = formset_factory(ManageInterviewForm,extra=1)

class ManageUgradPaperWorkForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    electee_exam_completed = forms.BooleanField(required=False)
    peer_interviews_completed = forms.IntegerField(min_value=0,validators=[max_peer_interviews_validator])
    character_essays_completed = forms.BooleanField(required=False,label="Interview Survey Completed")
    interviews_completed = forms.BooleanField(required=False)
    group_meetings = forms.IntegerField(min_value=0,label="Team Meetings")

ManageUgradPaperWorkFormSet = formset_factory(ManageUgradPaperWorkForm,extra=0)
    
class ManageActiveGroupMeetingsForm(Form):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=ElecteeGroup.get_current_leaders())
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
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_members())
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
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_members())
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

class AddActiveStatusForm(forms.ModelForm):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_actives())
    approve= forms.BooleanField(required=False)

    class Meta:
        model = Distinction
        exclude= ('term',)

    def save(self,commit=True):
        approved=self.cleaned_data.pop('approve',False)
        if approved:
            return super(AddActiveStatusForm, self).save(commit=commit)
        else:
            return None
class AddElecteeStatusForm(forms.ModelForm):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_electees())
    approve= forms.BooleanField(required=False)

    class Meta:
        model = Distinction
        exclude= ('term',)

    def save(self,commit=True):
        approved=self.cleaned_data.pop('approve',False)
        if approved:
            return super(AddActiveStatusForm, self).save(commit=commit)
        else:
            return None

ManageElecteeDAPAFormSet = modelformset_factory(Distinction,form=AddElecteeStatusForm)
ManageElecteeDAPAFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Electee').filter(Q(name__contains='DA')|Q(name__contains='PA'))

ElecteeToActiveFormSet = modelformset_factory(Distinction,form=AddElecteeStatusForm)
ElecteeToActiveFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Electee').exclude(Q(name__contains='DA')|Q(name__contains='PA'))


ManageActiveCurrentStatusFormSet = modelformset_factory(Distinction,form=AddActiveStatusForm)
ManageActiveCurrentStatusFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Active')
class ExternalServiceForm(forms.ModelForm):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_electees())

    class Meta:
        model = ProgressItem
        exclude = ('term','date_completed','event_type','related_event')

class TBPraiseForm(forms.ModelForm):
    recipient = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=UserProfile.get_users())

    class Meta:
        model = TBPraise
        exclude = ('giver','date_added','approved')
