from django.forms import Form
from django import forms
from django.forms.formsets import formset_factory
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory, BaseInlineFormSet

from electees.models import ElecteeGroup,EducationalBackgroundForm,BackgroundInstitution
from mig_main.models import get_electees
from history.models import Officer
from mig_main.utility import get_current_officers
from mig_main.default_values import get_current_term

def get_unassigned_electees():
    current_electee_groups = ElecteeGroup.objects.filter(term=get_current_term())
    current_electees = get_electees()
    for group in current_electee_groups.all():
        current_electees=current_electees.exclude(pk__in=group.members.all())
    return current_electees.order_by('standing','last_name')

class BaseInstituteFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        for form in self.forms:
            if 'degree_start_date' in form.cleaned_data and 'degree_end_date' in form.cleaned_data:
                if form.cleaned_data['degree_start_date']>form.cleaned_data['degree_end_date']:
                    raise ValidationError("The degree must have started before it can end.")

InstituteFormset = inlineformset_factory(EducationalBackgroundForm, BackgroundInstitution,formset=BaseInstituteFormSet,extra=1)

