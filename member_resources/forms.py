from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory
from django.db import IntegrityError
from django.db.models import Q


from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from electees.models import ElecteeGroup
from mig_main.models import AcademicTerm,Major,MemberProfile, TBPChapter,UserProfile,UserPreference,PREFERENCES,TBPraise
from history.models import  Distinction
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
        exclude=('user','uniqname','status','standing','init_chapter','alum_mail_freq','init_term','still_electing','edu_bckgrd_form')

class NonMemberProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user','uniqname')
class ConvertNonMemberToMemberForm(ModelForm):
    def save(self,userprofile,commit=True):
        if commit==False:
            raise IntegrityError('Saving logic complicated, commit must be enabled')
        if userprofile.is_member():
            raise IntegrityError('Model is already MemberProfile')
        # 1. clone profile
        uniqname = userprofile.uniqname
        marysuec = userprofile
        marysuec_user = userprofile.user
        marysuec_user.username = 'marysuec'
        marysuec_user.id=None
        marysuec_user.pk=None
        marysuec_user.save()
        marysuec.user=marysuec_user
        # 2. change uniqname to marysuec
        marysuec.uniqname = 'marysuec'
        marysuec.save()
        userprofile = UserProfile.objects.get(uniqname=uniqname)
        # 3. reassign all relationships of interest from profile A to marysuec
        nepp = userprofile.noneventprojectparticipant_set.all().distinct()
        shifts = userprofile.event_attendee.all().distinct()
        announcement_blurbs = userprofile.announcementblurb_set.all().distinct()
        waitlist_slot = userprofile.waitlistslot_set.all().distinct()
        itembring = userprofile.usercanbringpreferreditem_set.all().distinct()
        praise_giver = userprofile.praise_giver.all().distinct()
        praise_receiver = userprofile.praise_recipient.all().distinct()
        prefs = userprofile.userpreference_set.all().distinct()
        background_check = userprofile.backgroundcheck_set.all().distinct()
        
        for n in nepp:
            n.participant = marysuec
            n.save()
        
        for s in shifts:
            s.attendees.add(marysuec)
            s.attendees.remove(userprofile)
            
        for a in announcement_blurbs:
            a.contacts.add(marysuec)
            a.contacts.remove(userprofile)
        
        for w in waitlist_slot:
            w.user = marysuec
            w.save()
        
        for item in itembring:
            item.user = marysuec
            item.save()
            
        for p in praise_giver:
            p.giver = marysuec
            p.save()
            
        for p in praise_receiver:
            p.recipient = marysuec
            p.save()
            
        for p in prefs:
            p.user = marysuec
            p.save()
            
        for b in background_check:
            b.member = marysuec
            b.save()
            
        # 4. delete profile A
        userprofile.delete()
        
        # 5. create profile A'
        m = super(ConvertNonMemberToMemberForm, self).save(commit=False)
        m.uniqname = uniqname
        m.user = User.objects.get(username=uniqname)
        m.nickname = marysuec.nickname
        m.first_name = marysuec.first_name
        m.middle_name = marysuec.middle_name
        m.last_name = marysuec.last_name
        m.suffix = marysuec.suffix
        m.maiden_name = marysuec.maiden_name
        m.title = marysuec.title
        # 6. save profile A'
        m.save()
        
        # 7. reassign all relationships from profile marysuec to A'
        for n in nepp:
            n.participant = m
            n.save()
        
        for s in shifts:
            s.attendees.add(m)
            s.attendees.remove(marysuec)
            
        for a in announcement_blurbs:
            a.contacts.add(m)
            a.contacts.remove(marysuec)
        
        for w in waitlist_slot:
            w.user = m
            w.save()
        
        for item in itembring:
            item.user = m
            item.save()
            
        for p in praise_giver:
            p.giver = m
            p.save()
            
        for p in praise_receiver:
            p.recipient = m
            p.save()
            
        for p in prefs:
            p.user = m
            p.save()
            
        for b in background_check:
            b.member = m
            b.save()
        
        # 8. delete marysuec
        marysuec.delete()
        marysuec_user.delete()
class MemberProfileElecteeFromNonMemberForm(ConvertNonMemberToMemberForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    class Meta:
        model = MemberProfile
        exclude=('alum_mail_freq','edu_bckgrd_form','first_name',
                 'init_chapter','init_term','last_name',
                 'maiden_name','middle_name','nickname',
                 'standing','status','still_electing',
                 'suffix','title','uniqname','user')

class MemberProfileActiveFromNonMemberForm(ConvertNonMemberToMemberForm):
    major = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'element','placeholder':'Select Major(s)','closeOnSelect':True}),queryset=Major.objects.all().order_by('name'))
    class Meta:
        model = MemberProfile
        exclude=('edu_bckgrd_form','first_name',
                 'last_name',
                 'maiden_name','middle_name','nickname',
                 'status','still_electing',
                 'suffix','title','uniqname','user')

    

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
    group_meetings = forms.IntegerField(min_value=0,label="Team Meetings")

ManageUgradPaperWorkFormSet = formset_factory(ManageUgradPaperWorkForm,extra=0)
    
class ManageActiveGroupMeetingsForm(Form):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=ElecteeGroup.get_current_leaders())
    group_meetings = forms.IntegerField(min_value=0,label='Team Meetings')

ManageActiveGroupMeetingsFormSet = formset_factory(ManageActiveGroupMeetingsForm,extra=1)

class ManageGradPaperWorkForm(Form):
    electee = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    uniqname = forms.CharField(widget=forms.TextInput(attrs={'class':'disabled','readonly':'readonly'}))
    advisor_form_completed = forms.BooleanField(required=False)
    
ManageGradPaperWorkFormSet = formset_factory(ManageGradPaperWorkForm,extra=0)

class ManageProjectLeaderForm(Form):
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_members())
    is_project_leader = forms.BooleanField(required=False)
ManageProjectLeadersFormSet = formset_factory(ManageProjectLeaderForm,extra=3)

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
        approved=self.cleaned_data.pop('approve', False)
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
        approved=self.cleaned_data.pop('approve', False)
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
            return super(AddElecteeStatusForm, self).save(commit=commit)
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
