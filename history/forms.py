from django import forms
from django.forms.models import modelformset_factory

from django_select2 import ModelSelect2MultipleField,Select2MultipleWidget,ModelSelect2Field,Select2Widget

from history.models import Publication, WebsiteArticle,NonEventProject,NonEventProjectParticipant
from event_cal.models import EventPhoto
from mig_main.default_values import get_current_term
from mig_main.models import MemberProfile,AcademicTerm,OfficerPosition

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Publication

class WebArticleForm(forms.ModelForm):
#    tagged_members = ModelSelect2MultipleField()
    tagged_members = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'26em','placeholder':'Tag member(s)','closeOnSelect':True}),queryset=MemberProfile.get_members())
    class Meta:
        model = WebsiteArticle
        exclude = ['created_by']

class ProjectDescriptionForm(forms.Form):
    description = forms.CharField(widget=forms.Textarea)

class ProjectPhotoForm(forms.ModelForm):
    use_in_report = forms.BooleanField(required=False)
    class Meta:
        model = EventPhoto
        exclude = ['event','project_report']
    def __init__(self,*args,**kwargs):
        super(ProjectPhotoForm,self).__init__(*args,**kwargs)
        if self.instance.project_report:
            self.fields['use_in_report'].initial=True
        else:
            self.fields['use_in_report'].initial=False
    def save(self,commit=True):
        use_pic = self.cleaned_data.pop('use_in_report',False)
        m = super(ProjectPhotoForm,self).save(commit=False)
        if m.project_report and use_pic:
            if commit:
                m.save()
            return m
        elif m.project_report and not use_pic:
            m.project_report =None
            if commit:
                m.save()
            return m
        if m.event:
            m.project_report = m.event.project_report
        if commit:
            m.save()
        return m


ProjectPhotoFormset = modelformset_factory(EventPhoto,form = ProjectPhotoForm,extra=0)


class BaseNEPForm(forms.ModelForm):
    leaders = ModelSelect2MultipleField(widget=Select2MultipleWidget(select2_options={'width':'26em','placeholder':'Select Leader(s)','closeOnSelect':True}),queryset=MemberProfile.get_members())
    term = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'26em'}),queryset=AcademicTerm.get_rchron(),initial=get_current_term())
    assoc_officer = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'26em','placeholder':'Select Officer Position','closeOnSelect':True}),queryset=OfficerPosition.get_current(),label='Associated Officer')
    class Meta:
        model = NonEventProject

class BaseNEPParticipantForm(forms.ModelForm):
    participant = ModelSelect2Field(widget=Select2Widget(select2_options={'width':'26em','placeholder':'Select Participant','closeOnSelect':True}),queryset=MemberProfile.get_members())
    class Meta:
        model = NonEventProjectParticipant
