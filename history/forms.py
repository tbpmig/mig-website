from django import forms
from django.forms import ModelForm, BaseModelFormSet
from django.forms.models import modelformset_factory
from django.db.models import Q
from django_select2.forms import (
            ModelSelect2Widget,
            Select2Widget,
            ModelSelect2MultipleWidget,
            Select2MultipleWidget,
)

from history.models import (
            Award,
            BackgroundCheck,
            CommitteeMember,
            MeetingMinutes,
            NonEventProject,
            NonEventProjectParticipant,
            Officer,
            ProjectReportHeader,
            Publication,
            WebsiteArticle,
            Distinction,
            GoverningDocument,
            GoverningDocumentType
)
from event_cal.models import EventPhoto
from mig_main.models import (
            AcademicTerm,
            MemberProfile,
            OfficerPosition,
            UserProfile,
)
from requirements.models import DistinctionType

class GoverningDocumentForm(forms.ModelForm):
    """" Form for updating the governing documents"""
    class Meta:
        model = GoverningDocument
        exclude = ['active']

    def save(self, commit=True):
        gd = super(GoverningDocumentForm, self).save(commit=commit)
        if commit:
            gdt = gd.document_type
            gds = GoverningDocument.objects.filter(document_type=gdt)
            for gd_i in gds:
                gd_i.active = False
                gd_i.save()
            gd.active = True
            gd.save()


class AwardForm(forms.ModelForm):
    """ Form for giving out an award."""
    recipient = forms.ModelChoiceField(
                    widget=Select2Widget( ),
                    queryset=MemberProfile.get_members()
    )

    class Meta:
        model = Award
        fields = [
                'award_type',
                'term',
                'recipient',
                'comment'
        ]


class OfficerForm(forms.ModelForm):
    """ Form for specifying an officer.

    Excludes term, since that is specified externally.
    """
    user = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_members(),
                    label='Member'
    )
    position = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=OfficerPosition.get_current()
    )

    class Meta:
        model = Officer
        exclude = ['term']


class CommitteeMemberForm(forms.ModelForm):
    """ Form for adding committee members for a given term."""
    member = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_members(),
                    label='Member'
    )

    class Meta:
        model = CommitteeMember
        exclude = ['term']


class ArticleForm(forms.ModelForm):
    """ Form for submitting printed articles (Publications)"""
    class Meta:
        model = Publication
        fields = [
            'date_published',
            'volume_number',
            'edition_number',
            'name',
            'type',
            'pdf_file'
        ]


class WebArticleForm(forms.ModelForm):
    """ Form for submitting website articles."""
    TWEET_CHOICES = (
        ('N', 'No Tweet'),
        ('T', 'Tweet normally'),
        ('H', 'Tweet with #UmichEngin'),
    )
    tagged_members = forms.ModelMultipleChoiceField(
                        widget=Select2MultipleWidget(),
                        queryset=MemberProfile.get_members(),
                        required=False
    )
    tweet_option = forms.ChoiceField(choices=TWEET_CHOICES, initial='N')

    class Meta:
        model = WebsiteArticle
        exclude = ['created_by', 'approved']
        

class MeetingMinutesForm(forms.ModelForm):
    """ Form for submitting meeting minutes"""
    semester = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=AcademicTerm.get_rchron(),
                    initial=AcademicTerm.get_current_term()
    )

    class Meta:
        model = MeetingMinutes
        fields = [
            'pdf_file',
            'meeting_type',
            'semester',
            'meeting_name',
            'display_order'
        ]
        

class ProjectDescriptionForm(forms.Form):
    """ Form used to provide project description for a project report
    during compilation.
    """
    description = forms.CharField(widget=forms.Textarea)


class ProjectPhotoForm(forms.ModelForm):
    """ Form for associating photos with project reports during compilation.

    Overrides init to specify initial value for use_in_report based on whether
    the photo is associated with the project report or the event.

    Overrides save to associate or de-associate the photo with the project
    report based on the submitted value of use_in_report
    """
    use_in_report = forms.BooleanField(required=False)

    class Meta:
        model = EventPhoto
        exclude = ['event', 'project_report']

    def __init__(self, *args, **kwargs):
        super(ProjectPhotoForm, self).__init__(*args, **kwargs)
        if self.instance.project_report:
            self.fields['use_in_report'].initial = True
        else:
            self.fields['use_in_report'].initial = False

    def save(self, commit=True):
        use_pic = self.cleaned_data.pop('use_in_report', False)
        m = super(ProjectPhotoForm, self).save(commit=False)
        if m.project_report and use_pic:
            if commit:
                m.save()
            return m
        elif m.project_report and not use_pic:
            m.project_report = None
            if commit:
                m.save()
            return m
        if m.event:
            m.project_report = m.event.project_report
        if commit:
            m.save()
        return m


ProjectPhotoFormset = modelformset_factory(
                            EventPhoto,
                            form=ProjectPhotoForm,
                            extra=0
)


class BaseProjectReportHeaderForm(forms.ModelForm):
    """ Form for starting the project report compilation.
    """
    terms = forms.ModelMultipleChoiceField(
                    widget=Select2MultipleWidget(),
                    queryset=AcademicTerm.get_rchron()
    )
    preparer = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_actives()
    )

    class Meta:
        model = ProjectReportHeader
        exclude = [
            'finished_processing',
            'finished_photos',
            'last_processed',
            'last_photo'
        ]


class BaseNEPForm(forms.ModelForm):
    """ Base form for filling out a non-event project summary.
    """
    leaders = forms.ModelMultipleChoiceField(
                widget=Select2MultipleWidget(),
                queryset=MemberProfile.get_members()
    )
    term = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=AcademicTerm.get_rchron(),
                initial=AcademicTerm.get_current_term()
    )
    assoc_officer = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=OfficerPosition.get_current(),
                label='Associated Officer'
    )

    class Meta:
        model = NonEventProject
        fields = [
            'name',
            'description',
            'leaders',
            'assoc_officer',
            'term',
            'start_date',
            'end_date',
            'location'
        ]


class BaseNEPParticipantForm(forms.ModelForm):
    """ Base form for adding participants to a non-event project."""
    participant = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=MemberProfile.get_members()
    )

    class Meta:
        model = NonEventProjectParticipant
        fields = ['project', 'participant', 'hours']


class BaseBackgroundCheckForm(forms.ModelForm):
    """ Base form for adding member background checks.
    """
    member = forms.ModelChoiceField(
                widget=Select2Widget(),
                queryset=UserProfile.objects.all().order_by('last_name')
    )

    class Meta:
        model = BackgroundCheck
        exclude = ['date_added']


class MassAddBackgroundCheckForm(forms.Form):
    """ Form for quickly adding user background checks.
    """
    uniqnames = forms.CharField(
                    widget=forms.Textarea,
                    help_text='Separate uniqnames with a newline'
    )
    check_type = forms.ChoiceField(
                    choices=BackgroundCheck.CHECK_CHOICES
    )

    def save(self):
        """ Adds background checks for each uniqname in the list.
        If there is no profile for that uniqname, marks it and continues.
        """
        uniqnames = self.cleaned_data['uniqnames'].split('\n')
        no_profiles = []
        for uniqname in uniqnames:
            u = UserProfile.objects.filter(uniqname=uniqname.strip())
            if not u.exists():
                no_profiles.append(uniqname.strip())
                continue
            else:
                u = u[0]
            b = BackgroundCheck(
                    member=u,
                    check_type=self.cleaned_data['check_type']
            )
            b.save()
        if no_profiles:
            return no_profiles
        else:
            return None


class AddStatusForm(forms.ModelForm):
    member = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_actives()
    )
    approve = forms.BooleanField(required=False)

    class Meta:
        model = Distinction
        exclude= ('term',)
        
    def save(self, commit=True):
        approved = self.cleaned_data.pop('approve', False)
        if approved:
            return super(AddStatusForm, self).save(commit=commit)
        else:
            print 'unapproved'
            return None

class AddElecteeStatusForm(AddStatusForm):
    member = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_electees()
    )

class BaseAddStatusFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseAddStatusFormSet,
              self).__init__(*args, **kwargs)
        self.queryset = Distinction.objects.none()
    
    def save(self, term, commit=True):
        instances = super(BaseAddStatusFormSet, self).save(commit=False)
        if commit:
            for obj in self.deleted_objects:
                obj.delete()
            for instance in self.new_objects:
                if instance:
                    instance.term = term
                    if not Distinction.objects.filter(
                                        member=instance.member,
                                        distinction_type=instance.distinction_type,
                                        term=term).exists():
                        instance.save()
        return instances


class BaseAddActiveStatusFormSet(BaseAddStatusFormSet):
    def __init__(self, *args, **kwargs):
        term = kwargs.pop('term', AcademicTerm.get_current_term())
        initial=[]
        for distinction in DistinctionType.objects.filter(status_type__name='Active'):
            actives_already_received_distinction = MemberProfile.objects.filter(
                                distinction__distinction_type=distinction,
                                distinction__term=term
            )
            actives = distinction.get_actives_with_status(term)
            for active in actives:
                if active in actives_already_received_distinction:
                    continue
                if distinction.name == 'Active':
                    gift = 'N/A'
                else:
                    gift = 'Not specified'
                initial.append(
                    {
                        'member': active,
                        'distinction_type': distinction,
                        'gift': gift,
                        'approve': False
                    }
                )
        kwargs['initial'] = initial
        super(BaseAddActiveStatusFormSet,
              self).__init__(*args, **kwargs)
        self.extra = len(initial)+1
        self.form.base_fields['distinction_type'].queryset =\
                DistinctionType.objects.filter(status_type__name='Active')

ManageElecteeDAPAFormSet = modelformset_factory(Distinction,form=AddElecteeStatusForm)
ManageElecteeDAPAFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Electee').filter(Q(name__contains='DA')|Q(name__contains='PA'))
#ManageElecteeDAPAFormSet.form.base_fields['member'].queryset = MemberProfile.get_electees()

ElecteeToActiveFormSet = modelformset_factory(Distinction,form=AddElecteeStatusForm)
ElecteeToActiveFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Electee').exclude(Q(name__contains='DA')|Q(name__contains='PA'))
#ElecteeToActiveFormSet.form.base_fields['member'].queryset = MemberProfile.get_electees()

ManageActiveCurrentStatusFormSet = modelformset_factory(
                                                Distinction,
                                                form=AddStatusForm,
                                                formset=BaseAddActiveStatusFormSet
)