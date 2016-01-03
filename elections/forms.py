from django import forms
from django_select2 import (
        ModelSelect2Field,
        ModelSelect2MultipleField,
        Select2MultipleWidget,
        Select2Widget
)

from elections.models import Election, Nomination
from mig_main.models import OfficerPosition, MemberProfile


class NominationForm(forms.ModelForm):
    """ Form for submitting nominations.
    Overrides the default behavior to make it so that you can only nominate
    someone to a position that is part of the current election.
    """
    nominee = ModelSelect2Field(
                    widget=Select2Widget(
                            select2_options={
                                'width': 'element',
                                'placeholder': 'Select Nominee',
                                'closeOnSelect': True
                            }
                    ),
                    queryset=MemberProfile.get_members()
    )
    position = ModelSelect2Field(
                    widget=Select2Widget(
                            select2_options={
                                'width': 'element',
                                'placeholder': 'Select Position',
                                'closeOnSelect': True
                            }
                    ),
                    queryset=OfficerPosition.get_current()
    )

    class Meta:
        model = Nomination
        exclude = ('election', 'nominator', 'accepted',)

    def __init__(self, *args, **kwargs):
        election = kwargs.pop('election', None)
        super(NominationForm, self).__init__(*args, **kwargs)
        if election:
            officers = election.officers_for_election.all()
            self.fields['position'].queryset = officers


class ElectionForm(forms.ModelForm):
    """ Form for opening the election.
    Need to make it so that the initial values of officers_for_election
    are the officer positions that are enabled, electable, and are elected
    in the specified term.

    The only excluded field is the term, which is always* going to be the
    subsequent term.
    *except exceptions.
    """

    class Meta:
        model = Election
        fields = (
            'open_date',
            'close_date',
            'officers_for_election',
        )
