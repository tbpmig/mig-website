from django import forms
from elections.models import Election, Nomination, TempNomination
from mig_main.models import OfficerPosition

class NominationForm(forms.ModelForm):
	class Meta:
		model = Nomination
		exclude = ('election','nominator','accepted',)
		
	def clean(self):
		cleaned_data = super(NominationForm, self).clean()
		position_is_adv = cleaned_data.get("position")=="ADV"
		term_length = cleaned_data.get("term_length")
		if position_is_adv:
			if term_length==None or term_length<1 or term_length>6:
				raise forms.ValidationError("Nominations for advisor must include a term length of 1-6 semesters.")
		return cleaned_data


class TempNominationForm(forms.Form):
    nominee_name = forms.CharField(max_length=50)
    nominee_uniqname=forms.CharField(max_length=8)
    position = forms.ModelChoiceField(queryset=OfficerPosition.objects.exclude(name='Secretary').exclude(name='External Vice President').exclude(name='Website Officer'))
