from django.forms import Form
from django import forms
from django.forms.formsets import formset_factory
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.models import (
                    inlineformset_factory,
                    BaseInlineFormSet,
                    BaseModelFormSet,
                    modelformset_factory
)
from django.utils.translation import ugettext as _

from django_select2.forms import (
                    Select2MultipleWidget,
                    Select2Widget
)

from electees.models import (
                    ElecteeGroup,
                    EducationalBackgroundForm,
                    BackgroundInstitution,
                    SurveyQuestion,
                    ElecteeInterviewSurvey,
                    SurveyPart,
                    ElecteeInterviewFollowup
)
from mig_main.models import MemberProfile, AcademicTerm
from history.models import Officer
from mig_main.templatetags.my_markdown import my_markdown


def get_unassigned_electees():
    current_electee_groups = ElecteeGroup.objects.filter(
                                    term=AcademicTerm.get_current_term()
    )
    current_electees = MemberProfile.get_electees()
    for group in current_electee_groups.all():
        current_electees = current_electees.exclude(pk__in=group.members.all())
    return current_electees.order_by('standing', 'last_name')


class InterviewFollowupForm(forms.ModelForm):
    class Meta:
        model = ElecteeInterviewFollowup
        exclude = ['member', 'interview']

    def clean(self):
        cleaned_data = super(InterviewFollowupForm, self).clean()
        rec = cleaned_data.get('recommendation', None)
        if rec and (not rec == 'Y' and not cleaned_data.get('comments', None)):
            raise ValidationError('Comments are required for \'do not '
                                  'recommend\' or \'not sure\'')
        return cleaned_data


class BaseInstituteFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return
        for form in self.forms:
            if ('degree_start_date' in form.cleaned_data and
               'degree_end_date' in form.cleaned_data):
                start_date = form.cleaned_data['degree_start_date']
                end_date = form.cleaned_data['degree_end_date']
                if start_date > end_date:
                    raise ValidationError('The degree must have started '
                                          'before it can end.')


InstituteFormset = inlineformset_factory(
                        EducationalBackgroundForm,
                        BackgroundInstitution,
                        formset=BaseInstituteFormSet,
                        extra=1,
                        fields=[
                            'name',
                            'degree_type',
                            'major',
                            'degree_start_date',
                            'degree_end_date'
                        ]
)


class BaseElecteeGroupForm(forms.ModelForm):
    leaders = forms.ModelMultipleChoiceField(
                widget=Select2MultipleWidget(),
                queryset=MemberProfile.get_actives()
    )
    officers = forms.ModelMultipleChoiceField(
                widget=Select2MultipleWidget(),
                queryset=Officer.get_current_members()
    )

    class Meta:
        model = ElecteeGroup
        exclude = ('term', 'members', 'points',)


class ManualElecteeGroupMembersForm(forms.ModelForm):
    class meta:
        model = ElecteeGroup
        exclude = ['leaders', 'officers', 'points', 'term', 'members']
    group_name = forms.CharField(
                    widget=forms.TextInput(
                            attrs={
                                'class': 'disabled',
                                'readonly': 'readonly'
                            }
                    )
    )

    members_bulk = forms.CharField(
                        label='Member uniqnames (one per line)',
                        widget=forms.Textarea,
                        required=False
    )

    def clean(self):
        cleaned_data = super(ManualElecteeGroupMembersForm, self).clean()
        if any(self.errors):
            return
        members_bulk = cleaned_data.get('members_bulk', '')
        errors = []
        for uniqname in members_bulk.split('\n'):
            stripped_uniqname = uniqname.strip()
            if not stripped_uniqname:
                continue
            try:
                member = MemberProfile.objects.get(uniqname=stripped_uniqname)
                if member.electee_group_members.count():
                    errors.append(
                            ValidationError(
                                _('%(uniqname)s already in an electee team'),
                                code='duplicate',
                                params={'uniqname': stripped_uniqname}
                            )
                    )
                if not member.status.name == 'Electee':
                    errors.append(
                            ValidationError(
                                _('%(uniqname)s is not an electee'),
                                code='invalid',
                                params={'uniqname': stripped_uniqname}
                            )
                    )
            except ObjectDoesNotExist:
                errors.append(
                        ValidationError(
                            _('%(uniqname)s is not a member'),
                            code='invalid',
                            params={'uniqname': stripped_uniqname}
                        )
                )
        if errors:
            raise ValidationError(errors)
        return cleaned_data

    def save(self, commit=True):
        members_bulk = self.cleaned_data.pop('members_bulk', '')
        group = super(ManualElecteeGroupMembersForm, self).save(commit=commit)
        for uniqname in members_bulk.split('\n'):
            try:
                member = MemberProfile.objects.get(
                                uniqname=uniqname.lstrip().rstrip())
                group.members.add(member)
            except ObjectDoesNotExist:
                pass
        return group


class BaseManualElecteeGroupMembersFormSet(BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        uniqnames = set()
        errors = []
        for form in self.forms:
            group_uniqnames = form.cleaned_data['members_bulk'].split()
            for uniqname in group_uniqnames:
                stripped_uniqname = uniqname.strip()
                if not stripped_uniqname:
                    continue
                if stripped_uniqname in uniqnames:
                    errors.append(
                        ValidationError(
                            _('%(uniqname)s can only be added to one team'),
                            code='duplicate',
                            params={'uniqname': stripped_uniqname}
                        )
                    )
                else:
                    uniqnames.add(stripped_uniqname)
        if errors:
            raise ValidationError(errors)


ManualElecteeGroupMembersFormSet = modelformset_factory(
                                ElecteeGroup,
                                form=ManualElecteeGroupMembersForm,
                                exclude=[
                                        'leaders',
                                        'officers',
                                        'points',
                                        'term',
                                        'members'
                                ],
                                extra=0,
                                formset=BaseManualElecteeGroupMembersFormSet
)


class AddSurveyQuestionsForm(forms.ModelForm):
    questions = forms.ModelMultipleChoiceField(
                    widget=Select2MultipleWidget( ),
                    queryset=SurveyQuestion.objects.all().order_by(
                                                            'short_name')
    )

    class Meta:
        model = ElecteeInterviewSurvey
        exclude = ('term', 'due_date',)


class ElecteeSurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.questions = kwargs.pop('questions', [])
        init_answers = kwargs.pop('answers', [])
        initial = {"custom_%d" % answer.question.id: answer.answer
                   for answer in init_answers}
        kwargs['initial'] = initial
        super(ElecteeSurveyForm, self).__init__(*args, **kwargs)
        for question in self.questions:
            max_words = ('(Limit %s words)' % (question.max_words)
                         if question.max_words else '')
            self.fields["custom_%s" % question.id] = forms.CharField(
                                                widget=forms.Textarea,
                                                label=question.text+max_words,
                                                required=False
            )

    def get_answers(self):
        for name, value in self.cleaned_data.items():
            yield(
                SurveyQuestion.objects.get(id=name.replace("custom_", "")),
                value
            )

    def render(self):
        output = ''
        parts = SurveyPart.objects.filter(
                            surveyquestion__in=self.questions
        ).distinct()
        if self.non_field_errors():
            errors = '</li><li>'.join(self.non_field_errors())
            output += '<ul class=\"text-danger\"><li>%s</li></ul>' % errors
        for part in sorted(parts):
            output += "<h4>"+my_markdown(unicode(part))+"</h4>"
            if part.instructions:
                output += my_markdown(unicode(part.instructions))
            if part.number_of_required_questions is not None:
                if part.number_of_required_questions:
                    num_reqd = part.number_of_required_questions
                    output += ('<p>Please answer at least %d of the '
                               'following questions:</p>') % num_reqd
                else:
                    output += "<p>These questions are optional:<p>"
            else:
                output += "<p>Each question is required:</p>"
            output += "<ol>"
            questions = self.questions.filter(part=part).order_by(
                                                        'display_order'
            )
            for question in questions:
                lim_text = ''
                if question.max_words:
                    lim_text = '<strong>(Limit %d words)</strong>' % (
                                                    question.max_words)
                output += "<li><p for=\"id_custom_%d\">%s %s</p>" % (
                                    question.id,
                                    my_markdown(question.text),
                                    lim_text,
                )
                output += unicode(self["custom_%s" % question.id].errors)
                output += unicode(self["custom_%s" % question.id])
                output += "</li>"
            output += "</ol><hr/>"
        return output

    def clean(self):
        cleaned_data = super(ElecteeSurveyForm, self).clean()
        val_errors = []
        for name, value in self.cleaned_data.items():
            question = SurveyQuestion.objects.get(
                                    id=name.replace("custom_", "")
            )
            if (question.max_words and
               len(value.split()) > question.max_words):
                val_errors.append(
                        '%s: \"%s\" exceeded the maximum word '
                        'count (%d/%d words used)' % (
                                        unicode(question.part),
                                        question.short_name,
                                        len(value.split()),
                                        question.max_words
                        )
                )
        if val_errors:
            raise ValidationError(val_errors)
        return cleaned_data
