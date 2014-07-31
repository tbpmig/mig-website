from django import forms

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from elections.models import Election, Nomination
from mig_main.models import OfficerPosition,MemberProfile

class NominationForm(forms.ModelForm):
    nominee = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Nominee','closeOnSelect':True}),queryset=MemberProfile.get_members())
    position = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'element','placeholder':'Select Position','closeOnSelect':True}),queryset=OfficerPosition.get_current())
    class Meta:
        model = Nomination
        exclude = ('election','nominator','accepted',)
		
    def __init__(self, *args, **kwargs):
        election = kwargs.pop('election',None)
        super(NominationForm,self).__init__(*args,**kwargs)
        if election:
            self.fields['position'].queryset=election.officers_for_election.all()

#class TempNominationForm(forms.Form):
#    nominee_name = forms.CharField(max_length=50)
#    nominee_uniqname=forms.CharField(max_length=8)
#    position = forms.ModelChoiceField(queryset=OfficerPosition.objects.exclude(name='Secretary').exclude(name='External Vice President').exclude(name='Website Officer'))
