from django.forms import Form
from django import forms
from django.forms.formsets import formset_factory
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory, BaseInlineFormSet

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from electees.models import ElecteeGroup,EducationalBackgroundForm,BackgroundInstitution,SurveyQuestion,ElecteeInterviewSurvey,SurveyPart
from mig_main.models import MemberProfile,AcademicTerm
from history.models import Officer
from mig_main.templatetags.my_markdown import my_markdown
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
        
class ElecteeSurveyForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.questions = kwargs.pop('questions',[])
        init_answers = kwargs.pop('answers',[])
        initial = {"custom_%d"%answer.question.id:answer.answer for answer in init_answers}
        kwargs['initial']=initial
        super(ElecteeSurveyForm,self).__init__(*args,**kwargs)
        for question in self.questions:
            max_words = '(Limit %s words)'%(question.max_words) if question.max_words else ''
            self.fields["custom_%s"%question.id]=forms.CharField(widget=forms.Textarea,label=question.text+max_words,required=False)

    def get_answers(self):
        for name,value in self.cleaned_data.items():
            yield(SurveyQuestion.objects.get(id=name.replace("custom_","")),value)
    
    def render(self):
        output = ''
        parts = SurveyPart.objects.filter(surveyquestion__in=self.questions).distinct()
        if self.non_field_errors():
            output+="<ul class=\"text-danger\"><li>%s</li></ul>"%"</li><li>".join(self.non_field_errors())
        for part in sorted(parts):
            output+="<h4>"+my_markdown(unicode(part))+"</h4>"
            if not part.number_of_required_questions is None:
                if part.number_of_required_questions:
                    output+="<p>Please answer at least %d of the following questions:</p>"%part.number_of_required_questions
                else:
                    output+="<p>These questions are optional:<p>"
            else:
                output+="<p>Each question is required:</p>"
            output+="<ol>"
            questions = self.questions.filter(part=part).order_by('display_order')
            for question in questions:
                output+="<li><p for=\"id_custom_%d\">%s %s</p>"%(question.id,my_markdown(question.text),"<strong>(Limit %d words)</strong>"%(question.max_words) if question.max_words else "")
                output+=unicode(self["custom_%s"%question.id].errors)
                output+=unicode(self["custom_%s"%question.id])
                output+="</li>"
            output+="</ol><hr/>"
        return output
    def clean(self):
        cleaned_data = super(ElecteeSurveyForm,self).clean()
        val_errors = []
        for name,value in self.cleaned_data.items():
            question = SurveyQuestion.objects.get(id=name.replace("custom_",""))
            if question.max_words and len(value.split())>question.max_words:
                val_errors.append("%s: \"%s\" exceeded the maximum word count (%d/%d words used)"%(unicode(question.part),question.short_name,len(value.split()),question.max_words))
        if val_errors:
            raise ValidationError(val_errors)
        return cleaned_data



    