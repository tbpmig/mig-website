from django.forms import ModelForm, Form
from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.models import modelformset_factory
from django.db.models import Q


from django_select2 import ModelSelect2Field, Select2Widget

from electees.models import ElecteeGroup
from mig_main.models import MemberProfile, UserProfile, TBPraise
from history.models import  Distinction
from requirements.models import (
                ProgressItem,
)


    
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
