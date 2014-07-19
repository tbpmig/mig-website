from django import forms
from django.forms.models import modelformset_factory
from history.models import Publication, WebsiteArticle
from event_cal.models import EventPhoto

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Publication

class WebArticleForm(forms.ModelForm):
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
