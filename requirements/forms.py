from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Q
from django.forms import ModelForm, BaseModelFormSet, Form, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory, formset_factory

from django_select2 import ModelSelect2Field, Select2Widget

from history.models import Officer
from requirements.models import ProgressItem, EventCategory, Requirement, DistinctionType
from mig_main.models import AcademicTerm, MemberProfile
from mig_main.utility import get_current_group_leaders, get_current_event_leaders
from electees.models import ElecteeGroup

def max_peer_interviews_validator(value):
    requirement = Requirement.objects.filter(
                    event_category__name='Peer Interviews')
    if requirement:
        if value > requirement[0].amount_required:
            raise ValidationError(
                u'This value cannot exceed %s' % requirement[0].amount_required
            )


class ManageDuesForm(ModelForm):
    electee = forms.CharField(
                        widget=forms.TextInput(
                                attrs={
                                    'class': 'disabled',
                                    'readonly': 'readonly'
                                }
                        )
    )
    uniqname = forms.CharField(
                        widget=forms.TextInput(
                                attrs={
                                    'class': 'disabled',
                                    'readonly': 'readonly'
                                }
                        )
    )
    dues_paid = forms.BooleanField(required=False)
    
    class Meta:
        model = ProgressItem
        fields = ['electee', 'uniqname', 'dues_paid']

    def __init__(self, *args, **kwargs):
        super(ManageDuesForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['electee'].initial = self.instance.member.get_firstlast_name()
            self.fields['uniqname'].initial = self.instance.member.uniqname
            self.fields['dues_paid'].initial = self.instance.amount_completed>0

    def save(self, commit=True):
        dues_paid = self.cleaned_data.pop('dues_paid', False)
        uniqname = self.cleaned_data.pop('uniqname', False)
        self.cleaned_data.pop('electee', False)
        instance = super(ManageDuesForm, self).save(commit=False)
        if dues_paid:
            instance.amount_completed = 1
        else:
            instance.amount_completed = 0
        if commit:
            instance.save()
        return instance
    
class BaseManageDuesFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseManageDuesFormSet,
              self).__init__(*args, **kwargs)

        #create filtering here whatever that suits you needs
        self.queryset = ProgressItem.objects.filter(
                                member__status__name='Electee',
                                event_type__name='Dues',
                                term=AcademicTerm.get_current_term(),
                            ).order_by(
                                'member__last_name',
                                'member__first_name',
                                'member__uniqname'
                            )

ManageDuesFormSet = modelformset_factory(
                        ProgressItem,
                        form=ManageDuesForm,
                        formset=BaseManageDuesFormSet,
                        extra=0
)
class ManageActiveGroupMeetingsForm(ModelForm):
    member = ModelSelect2Field(
                widget=Select2Widget(
                        select2_options={
                                'width': 'element',
                                'placeholder': 'Select Member',
                                'closeOnSelect': True
                        }
                ),
                queryset=ElecteeGroup.get_current_leaders()
    )
    amount_completed = forms.IntegerField(min_value=0, label='Team Meetings')
    class Meta:
        model = ProgressItem
        fields = ['member', 'amount_completed']

    def __init__(self, *args, **kwargs):
        extra_amt = 0
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        init_val = int(0)
        if instance:
            extra_meetings = ProgressItem.objects.filter(
                                    term=AcademicTerm.get_current_term(),
                                    member=instance.member,
                                    event_type__name='Extra Team Meetings',
            )
            if extra_meetings.exists():
                extra_amt = extra_meetings.aggregate(Sum('amount_completed'))
                extra_amt = extra_amt['amount_completed__sum']
            init_val = int(instance.amount_completed + extra_amt)

        initial['amount_completed'] = init_val
        kwargs['initial']=initial
        super(ManageActiveGroupMeetingsForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super(ManageActiveGroupMeetingsForm, self).save(commit=False)
        term = AcademicTerm.get_current_term()
        instance.term = term
        instance.date_completed=date.today()
        instance.name='Team Meetings'
        extra_meetings = ProgressItem.objects.filter(
                            term=term,
                            member=instance.member,
                            event_type__name='Extra Team Meetings',
        )
        group = ElecteeGroup.objects.filter(Q(leaders=instance.member) |
                                            Q(officers=instance.member))
        group = group.filter(term=term)
        dist = DistinctionType.objects.filter(
                        status_type__name='Electee',
                        standing_type__name='Undergraduate')
        if group.exists():
            print group
            if group[0].members.exists():
                print group[0]
                standing=group[0].members.all()[0].standing
                dist = DistinctionType.objects.filter(
                        status_type__name='Electee',
                        standing_type=standing)
        group_meeting_req = Requirement.objects.filter(
                distinction_type=dist,
                event_category__name='Team Meetings',
                term=term.semester_type)
        if group_meeting_req:
            amount_group_req = group_meeting_req[0].amount_required
        else:
            amount_group_req = 0
        if extra_meetings.count() > 1 or instance.amount_completed <= amount_group_req:
            extra_meetings.delete()
        
        if not extra_meetings.exists() and instance.amount_completed > amount_group_req:
            extra_meeting = ProgressItem(
                            term=term,
                            member=instance.member,
                            date_completed=date.today()
            )
            extra_meeting.event_type = EventCategory.objects.get(
                                            name='Extra Team Meetings')
            extra_meeting.amount_completed = instance.amount_completed - amount_group_req
            extra_meeting.save()
        elif instance.amount_completed > amount_group_req:
            extra_meeting = extra_meetings[0]
            extra_meeting.amount_completed = instance.amount_completed - amount_group_req
            extra_meeting.save()
        instance.event_type = EventCategory.objects.get(name='Team Meetings')
        if instance.amount_completed > amount_group_req:
            instance.amount_completed = amount_group_req
        if commit:
            instance.save()
        return instance

class BaseManageActiveGroupMeetingsFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseManageActiveGroupMeetingsFormSet,
              self).__init__(*args, **kwargs)

        self.queryset = ProgressItem.objects.filter(
                                member__status__name='Active',
                                event_type__name='Team Meetings',
                                term=AcademicTerm.get_current_term(),
                            ).order_by(
                                'member__last_name',
                                'member__first_name',
                                'member__uniqname'
                            )


ManageActiveGroupMeetingsFormSet = modelformset_factory(
                        ProgressItem,
                        form=ManageActiveGroupMeetingsForm,
                        formset=BaseManageActiveGroupMeetingsFormSet,
                        extra=1
)

class ManageUgradPaperWorkForm(Form):
    electee = forms.CharField(
                    widget=forms.TextInput(
                            attrs={
                                'class': 'disabled',
                                'readonly': 'readonly'
                            }
                    )
    )
    standing = forms.CharField(
                        widget=forms.TextInput(
                                attrs={
                                    'class': 'disabled',
                                    'readonly': 'readonly'
                                }
                        )
    )
    uniqname = forms.CharField(
                    widget=forms.TextInput(
                            attrs={
                                'class': 'disabled',
                                'readonly': 'readonly'
                            }
                    )
    )
    electee_exam_completed = forms.BooleanField(required=False)
    peer_interviews_completed = forms.IntegerField(
                                    min_value=0,
                                    validators=[max_peer_interviews_validator]
    )
    group_meetings = forms.IntegerField(
                                min_value=0,
                                label='Team Meetings'
    )
    advisor_form = forms.BooleanField(
                                required=False,
                                label='Grad Advisor Form'
    )
    def save_helper(self,
                    profile,
                    p_field,
                    term,
                    event_type_name,
                    progress_name,
                    is_boolean=False,
                    secondary_type=None,
                    primary_max=None):
        event_type = EventCategory.objects.get(name=event_type_name)
        existing_progress = ProgressItem.objects.filter(
                                member=profile,
                                term=term,
                                event_type=event_type,
        )
        if p_field:
            if is_boolean:
                amount_completed = 1.0
            else:
                amount_completed = Decimal(p_field)

            if existing_progress.count() > 1:
                existing_progress.delete()

            if not existing_progress.exists():
                # this handles the first if statement too
                p = ProgressItem(
                        member=profile,
                        term=term,
                        amount_completed=amount_completed,
                        date_completed=date.today(),
                        name=progress_name,
                        event_type=event_type,
                )
            else:
                p = existing_progress[0]
                p.amount_completed = amount_completed

            p.save()
            if secondary_type and primary_max:
                secondary_amount = 0
                if p.amount_completed > primary_max:
                    p.amount_completed = primary_max
                    p.save()
                    secondary_amount = amount_completed - primary_max
                self.save_helper(
                            profile,
                            secondary_amount,
                            term,
                            seconary_type,
                            secondary_type + ' Completed',
                )
                    
        else:
            existing_progress.delete()
    def save(self, commit=True):
        uniqname = self.cleaned_data['uniqname']
        profile = MemberProfile.objects.get(uniqname=uniqname)
        term = AcademicTerm.get_current_term()
        if not profile:
            return
        self.save_helper(
                    profile,
                    self.cleaned_data.pop('electee_exam_completed', None),
                    term,
                    'Electee Exam',
                    'Electee Exam Completed',
                    is_boolean=True,
        )
        self.save_helper(
                    profile,
                    self.cleaned_data.pop('peer_interviews_completed', None),
                    term,
                    'Peer Interviews',
                    'Peer Interviews Completed'
        )
        dist = DistinctionType.objects.filter(
                status_type__name='Electee',
                standing_type=profile.standing)
        group_meeting_req = Requirement.objects.filter(
                distinction_type=dist,
                event_category__name='Team Meetings',
                term=term.semester_type)
        if group_meeting_req:
            amount_group_req = group_meeting_req[0].amount_required
        else:
            amount_group_req = 0
        self.save_helper(
                    profile,
                    self.cleaned_data.pop('group_meetings', None),
                    term,
                    'Team Meetings',
                    'Team Meetings Completed',
                    secondary_type='Extra Team Meetings',
                    primary_max=amount_group_req,
        )       
        self.save_helper(
                    profile,
                    self.cleaned_data.pop('advisor_form', None),
                    term,
                    'Advisor Form',
                    'Advisor Form Completed',
                    is_boolean=True,
        )
class BaseManageUgradPaperWorkFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        profiles = kwargs.pop('profiles', None)
        exam_name = kwargs.pop('exam_name', None)
        interview_name = kwargs.pop('interview_name', None)
        group_meetings_name = kwargs.pop('group_meetings_name', None)
        advisor_form_name = kwargs.pop('advisor_form_name', None)
        if not profiles:
            return
        initial = []
        term = AcademicTerm.get_current_term()
        for profile in profiles:
            init_dict = {'electee': profile.get_firstlast_name(),
                         'standing': profile.standing.name,
                         'uniqname': profile.uniqname}
            
            exam_progress = ProgressItem.objects.filter(
                            event_type__name=exam_name,
                            term=term,
                            member=profile,
            ).aggregate(Sum('amount_completed'))
            if exam_progress['amount_completed__sum'] > 0:
                init_dict['electee_exam_completed'] = True
            else:
                init_dict['electee_exam_completed'] = False
            interview_progress = ProgressItem.objects.filter(
                                event_type__name=interview_name,
                                term=term,
                                member=profile,
            ).aggregate(Sum('amount_completed'))
            amount = interview_progress['amount_completed__sum']
            init_dict['peer_interviews_completed'] = int(amount) if amount else 0
                            
            group_meetings_progress = ProgressItem.objects.filter(
                                event_type__name__in=group_meetings_name,
                                term=term,
                                member=profile,
            ).aggregate(Sum('amount_completed'))
            amount = group_meetings_progress['amount_completed__sum']
            init_dict['group_meetings'] = int(amount) if amount else 0
            advisor_form_progress = ProgressItem.objects.filter(
                            event_type__name=advisor_form_name,
                            term=term,
                            member=profile,
            ).aggregate(Sum('amount_completed'))
            if advisor_form_progress['amount_completed__sum'] > 0:
                init_dict['advisor_form'] = True
            else:
                init_dict['advisor_form'] = False
            initial.append(init_dict)
        kwargs['initial']=initial
        print initial
        super(BaseManageUgradPaperWorkFormSet, self).__init__(*args, **kwargs)
    
    def save(self):
        for form in self:
            form.save()

ManageUgradPaperWorkFormSet = formset_factory(form=ManageUgradPaperWorkForm,formset=BaseManageUgradPaperWorkFormSet,extra=0)


class LeadershipCreditForm(forms.ModelForm):
    member = ModelSelect2Field(
                widget=Select2Widget(
                select2_options={
                        'width': 'element',
                        'placeholder': 'Select Member',
                        'closeOnSelect': True
                }),
                queryset=MemberProfile.get_members()
    )
    approve = forms.BooleanField(required=False)

    class Meta:
        model = ProgressItem
        exclude= (
                'term',
                'event_type',
                'amount_completed',
                'date_completed',
                'related_event'
        )
    
    def save(self, commit=True):
        approved = self.cleaned_data.pop('approve', False)
        if approved:
            instance = super(LeadershipCreditForm, self).save(commit=False)
            instance.term = AcademicTerm.get_current_term()
            instance.event_type = EventCategory.objects.get(name='Leadership')
            instance.amount_completed = 1
            instance.date_completed = date.today() 
            if commit:
                instance.save()
            return instance
        else:
            return None


class BaseLeadershipCreditFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        initial=[]
        group_leaders = get_current_group_leaders()
        event_leaders = get_current_event_leaders()
        officers = Officer.get_current_members()
        leader_list = group_leaders |event_leaders |officers
        for leader in leader_list:
            if ProgressItem.objects.filter(
                                member=leader,
                                term=AcademicTerm.get_current_term(),
                                event_type=EventCategory.objects.get(
                                                        name='Leadership')
                    ).exists():
                continue
            if leader in officers:
                name_str = 'Was an officer'
            elif leader in group_leaders:
                name_str = 'Was a group leader'
            else:
                name_str = 'Led a project'
            initial.append({'member':leader, 'name':name_str})
        kwargs['initial'] = initial
        super(BaseLeadershipCreditFormSet,
              self).__init__(*args, **kwargs)

        self.queryset = ProgressItem.objects.none()
        self.extra = len(initial) + 1


LeadershipCreditFormSet = modelformset_factory(
                                    ProgressItem,
                                    form=LeadershipCreditForm,
                                    formset=BaseLeadershipCreditFormSet
)