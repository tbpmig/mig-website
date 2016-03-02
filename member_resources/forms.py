from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelformset_factory
from django.db.models import Q


from django_select2 import ModelSelect2Field, Select2Widget

from electees.models import ElecteeGroup
from member_resources.models import ProjectLeaderList
from mig_main.models import MemberProfile, UserProfile, TBPraise
from history.models import  Distinction
from requirements.models import (
                ProgressItem,
                DistinctionType,
)

class MassAddForm(Form):
    uniqnames = forms.CharField(widget=forms.Textarea)


class ManageProjectLeaderForm(ModelForm):
    member_profile = ModelSelect2Field(
                        widget=Select2Widget(
                            select2_options={
                                    'width': 'element',
                                    'placeholder': 'Select Member',
                                    'closeOnSelect': True
                            }
                        ),
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
    member = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=MemberProfile.get_electees())

    class Meta:
        model = ProgressItem
        exclude = ('term','date_completed','event_type','related_event')

class TBPraiseForm(forms.ModelForm):
    recipient = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Member','closeOnSelect':True}),queryset=UserProfile.get_users())

    class Meta:
        model = TBPraise
        exclude = ('giver','date_added','approved')
