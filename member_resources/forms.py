from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelformset_factory
from django.db.models import Q


from django_select2.forms import Select2Widget

from electees.models import ElecteeGroup
from member_resources.models import ProjectLeaderList
from mig_main.models import MemberProfile, UserProfile, TBPraise
from history.models import Distinction
from requirements.models import (
                ProgressItem,
                DistinctionType,
)


class MassAddForm(Form):
    uniqnames = forms.CharField(widget=forms.Textarea)


class ManageProjectLeaderForm(ModelForm):
    member_profile = forms.ModelChoiceField(
                        widget=Select2Widget(),
                        queryset=MemberProfile.get_members()
    )

    class Meta:
        model = ProjectLeaderList
        fields = ['member_profile']


ManageProjectLeadersFormSet = modelformset_factory(
                                    ProjectLeaderList,
                                    form=ManageProjectLeaderForm,
                                    extra=3,
                                    can_delete=True
)


class ExternalServiceForm(forms.ModelForm):
    member = forms.ModelChoiceField(
                        widget=Select2Widget(),
                        queryset=MemberProfile.get_electees()
    )

    class Meta:
        model = ProgressItem
        exclude = ('term', 'date_completed', 'event_type', 'related_event')


class TBPraiseForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=UserProfile.get_users()
    )

    class Meta:
        model = TBPraise
        exclude = ('giver', 'date_added', 'approved')
