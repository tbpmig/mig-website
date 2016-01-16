from datetime import date
from decimal import Decimal

from django import forms
from django.db.models import Sum
from django.forms import ModelForm, BaseModelFormSet, Form, BaseFormSet
from django.core.exceptions import ValidationError
from django.forms.models import modelformset_factory, formset_factory

from requirements.models import ProgressItem, EventCategory, Requirement, DistinctionType
from mig_main.models import AcademicTerm, MemberProfile


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
                                event_type__name='Dues'
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
                print p_field
                print p_field.__class__
                print ''
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
