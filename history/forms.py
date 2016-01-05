from django import forms
from django.forms.models import modelformset_factory

from django_select2 import (
            ModelSelect2Field,
            ModelSelect2MultipleField,
            Select2MultipleWidget,
            Select2Widget,
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
)
from event_cal.models import EventPhoto
from mig_main.models import (
            AcademicTerm,
            MemberProfile,
            OfficerPosition,
            UserProfile,
)


class AwardForm(forms.ModelForm):
    """ Form for giving out an award."""
    recipient = ModelSelect2Field(
                    widget=Select2Widget(
                            select2_options={
                                    'width': 'element',
                                    'placeholder': 'Select member',
                                    'closeOnSelect': True
                            }
                    ),
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
    user = ModelSelect2Field(
                    widget=Select2Widget(
                        select2_options={
                                'width': 'element',
                                'placeholder': 'Select member',
                                'closeOnSelect': True
                        }
                    ),
                    queryset=MemberProfile.get_members(),
                    label='Member'
    )
    position = ModelSelect2Field(
                    widget=Select2Widget(
                        select2_options={
                                'width': 'element',
                                'placeholder': 'Select member',
                                'closeOnSelect': True
                        }
                    ),
                    queryset=OfficerPosition.get_current()
    )

    class Meta:
        model = Officer
        exclude = ['term']


class CommitteeMemberForm(forms.ModelForm):
    """ Form for adding committee members for a given term."""
    member = ModelSelect2Field(
                    widget=Select2Widget(
                        select2_options={
                                'width': 'element',
                                'placeholder': 'Select member',
                                'closeOnSelect': True
                        }
                    ),
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
    tagged_members = ModelSelect2MultipleField(
                        widget=Select2MultipleWidget(
                            select2_options={
                                'width': '26em',
                                'placeholder': 'Tag member(s)',
                                'closeOnSelect': True
                            }
                        ),
                        queryset=MemberProfile.get_members(),
                        required=False
    )
    tweet_option = forms.ChoiceField(choices=TWEET_CHOICES, initial='N')

    class Meta:
        model = WebsiteArticle
        exclude = ['created_by', 'approved']


class MeetingMinutesForm(forms.ModelForm):
    """ Form for submitting meeting minutes"""
    semester = ModelSelect2Field(
                    widget=Select2Widget(
                        select2_options={
                            'width': '10em',
                            'placeholder': 'Select Term',
                            'closeOnSelect': True
                        }
                    ),
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
    terms = ModelSelect2MultipleField(
                    widget=Select2MultipleWidget(
                        select2_options={
                                'width': '26em',
                                'placeholder': 'Select Term(s)',
                                'closeOnSelect': True
                        }
                    ),
                    queryset=AcademicTerm.get_rchron()
    )
    preparer = ModelSelect2Field(
                    widget=Select2Widget(
                        select2_options={
                                'width': '26em'
                        }
                    ),
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
    leaders = ModelSelect2MultipleField(
                widget=Select2MultipleWidget(
                    select2_options={
                            'width': '26em',
                            'placeholder': 'Select Leader(s)',
                            'closeOnSelect':
                            True
                    }
                ),
                queryset=MemberProfile.get_members()
    )
    term = ModelSelect2Field(
                widget=Select2Widget(
                    select2_options={
                            'width': '26em'
                    }
                ),
                queryset=AcademicTerm.get_rchron(),
                initial=AcademicTerm.get_current_term()
    )
    assoc_officer = ModelSelect2Field(
                widget=Select2Widget(
                    select2_options={
                            'width': '26em',
                            'placeholder': 'Select Officer Position',
                            'closeOnSelect': True
                    }
                ),
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
    participant = ModelSelect2Field(
                widget=Select2Widget(
                    select2_options={
                            'width': '26em',
                            'placeholder': 'Select Participant',
                            'closeOnSelect': True
                    }
                ),
                queryset=MemberProfile.get_members()
    )

    class Meta:
        model = NonEventProjectParticipant
        fields = ['project', 'participant', 'hours']


class BaseBackgroundCheckForm(forms.ModelForm):
    """ Base form for adding member background checks.
    """
    member = ModelSelect2Field(
                widget=Select2Widget(
                    select2_options={
                            'width': '26em',
                            'placeholder': 'Select Participant',
                            'closeOnSelect': True
                    }
                ),
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
