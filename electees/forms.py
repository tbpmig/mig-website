from django.forms import Form
from django import forms
from django.forms.formsets import formset_factory
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory, BaseInlineFormSet

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from electees.models import ElecteeGroup,EducationalBackgroundForm,BackgroundInstitution,SurveyQuestion,ElecteeInterviewSurvey
from mig_main.models import MemberProfile,AcademicTerm
from history.models import Officer

def get_unassigned_electees():
    current_electee_groups = ElecteeGroup.objects.filter(term=AcademicTerm.get_current_term())
    current_electees = MemberProfile.get_electees()
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

class BaseElecteeGroupForm(forms.ModelForm):
#    tagged_members = ModelSelect2MultipleField()
    leaders = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'26em','placeholder':'Select leader(s)','closeOnSelect':True}),queryset=MemberProfile.get_actives())
    officers = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'26em','placeholder':'Select officer liaison(s)','closeOnSelect':True}),queryset=Officer.get_current_members())
    class Meta:
        model = ElecteeGroup
        exclude= ('term','members','points',)

class AddSurveyQuestionsForm(forms.ModelForm):
    questions = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'26em','placeholder':'Select question(s)','closeOnSelect':True}),queryset=SurveyQuestion.objects.all().order_by('short_name'))
    class Meta:
        model = ElecteeInterviewSurvey
        exclude=('term','due_date',)