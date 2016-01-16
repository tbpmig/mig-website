from django.contrib.auth.models import User
from django import forms
from django.forms import ModelForm, BaseModelFormSet
from django.forms.models import modelformset_factory
from django.db import IntegrityError

from django_select2 import (
            ModelSelect2MultipleField,
            Select2MultipleWidget,
            ModelSelect2Field,
            Select2Widget,
)

from electees.models import electee_stopped_electing
from mig_main.models import (
            AcademicTerm,
            Major,
            MemberProfile,
            UserProfile,
            TBPChapter,
)


class MemberProfileForm(ModelForm):
    major = ModelSelect2MultipleField(
                widget=Select2MultipleWidget(
                            select2_options={
                                    'width': 'element',
                                    'placeholder': 'Select Major(s)',
                                    'closeOnSelect': True
                            }
                ),
                queryset=Major.objects.all().order_by('name')
    )

    class Meta:
        model = MemberProfile
        exclude = (
                'user',
                'uniqname',
                'status',
                'UMID',
                'still_electing',
                'edu_bckgrd_form'
        )


class ElecteeProfileForm(MemberProfileForm):
    class Meta:
        model = MemberProfile
        exclude = (
                'user',
                'uniqname',
                'status',
                'init_chapter',
                'UMID',
                'init_term',
                'still_electing',
                'standing',
                'alum_mail_freq',
                'job_field',
                'employer',
                'meeting_speak',
                'edu_bckgrd_form'
        )


class MemberProfileNewActiveForm(MemberProfileForm):
    init_term = ModelSelect2Field(
                    widget=Select2Widget(
                            select2_options={
                                    'width': '12em',
                                    'placeholder': 'Select Term',
                                    'closeOnSelect': True
                            }
                    ),
                    queryset=AcademicTerm.get_rchron(),
                    label='Initiation Term'
    )
    init_chapter = ModelSelect2Field(
                    widget=Select2Widget(
                            select2_options={
                                    'width': '10em',
                                    'placeholder': 'Select Chapter',
                                    'closeOnSelect': True
                            }
                    ),
                    queryset=TBPChapter.objects.all(),
                    label='Initiating Chapter'
    )

    class Meta:
        model = MemberProfile
        exclude = (
            'user',
            'uniqname',
            'status',
            'edu_bckgrd_form',
            'still_electing'
        )


class MemberProfileNewElecteeForm(MemberProfileForm):
    class Meta:
        model = MemberProfile
        exclude = (
                'user',
                'uniqname',
                'status',
                'standing',
                'init_chapter',
                'alum_mail_freq',
                'init_term',
                'still_electing',
                'edu_bckgrd_form'
        )


class NonMemberProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user', 'uniqname')


class ConvertNonMemberToMemberForm(MemberProfileForm):
    def save(self, userprofile, commit=True):
        if commit is False:
            raise IntegrityError(
                    'Saving logic complicated, commit must be enabled')
        if userprofile.is_member():
            raise IntegrityError('Model is already MemberProfile')
        # 1. clone profile
        uniqname = userprofile.uniqname
        marysuec = userprofile
        marysuec_user = userprofile.user
        marysuec_user.username = 'marysuec'
        marysuec_user.id = None
        marysuec_user.pk = None
        marysuec_user.save()
        marysuec.user = marysuec_user
        # 2. change uniqname to marysuec
        marysuec.uniqname = 'marysuec'
        marysuec.save()
        userprofile = UserProfile.objects.get(uniqname=uniqname)
        # 3. reassign all relationships of interest from profile A to marysuec
        nepp = userprofile.noneventprojectparticipant_set.all().distinct()
        shifts = userprofile.event_attendee.all().distinct()
        announcement_blurbs = userprofile.announcementblurb_set.all(
                                                            ).distinct()
        waitlist_slot = userprofile.waitlistslot_set.all().distinct()
        itembring = userprofile.usercanbringpreferreditem_set.all().distinct()
        praise_giver = userprofile.praise_giver.all().distinct()
        praise_receiver = userprofile.praise_recipient.all().distinct()
        prefs = userprofile.userpreference_set.all().distinct()
        background_check = userprofile.backgroundcheck_set.all().distinct()

        for n in nepp:
            n.participant = marysuec
            n.save()

        for s in shifts:
            s.attendees.add(marysuec)
            s.attendees.remove(userprofile)

        for a in announcement_blurbs:
            a.contacts.add(marysuec)
            a.contacts.remove(userprofile)

        for w in waitlist_slot:
            w.user = marysuec
            w.save()

        for item in itembring:
            item.user = marysuec
            item.save()

        for p in praise_giver:
            p.giver = marysuec
            p.save()

        for p in praise_receiver:
            p.recipient = marysuec
            p.save()

        for p in prefs:
            p.user = marysuec
            p.save()

        for b in background_check:
            b.member = marysuec
            b.save()

        # 4. delete profile A
        userprofile.delete()

        # 5. create profile A'
        m = super(ConvertNonMemberToMemberForm, self).save(commit=False)
        m.uniqname = uniqname
        m.user = User.objects.get(username=uniqname)
        m.nickname = marysuec.nickname
        m.first_name = marysuec.first_name
        m.middle_name = marysuec.middle_name
        m.last_name = marysuec.last_name
        m.suffix = marysuec.suffix
        m.maiden_name = marysuec.maiden_name
        m.title = marysuec.title
        # 6. save profile A'
        m.save()

        # 7. reassign all relationships from profile marysuec to A'
        for n in nepp:
            n.participant = m
            n.save()

        for s in shifts:
            s.attendees.add(m)
            s.attendees.remove(marysuec)

        for a in announcement_blurbs:
            a.contacts.add(m)
            a.contacts.remove(marysuec)

        for w in waitlist_slot:
            w.user = m
            w.save()

        for item in itembring:
            item.user = m
            item.save()

        for p in praise_giver:
            p.giver = m
            p.save()

        for p in praise_receiver:
            p.recipient = m
            p.save()

        for p in prefs:
            p.user = m
            p.save()

        for b in background_check:
            b.member = m
            b.save()

        # 8. delete marysuec
        marysuec.delete()
        marysuec_user.delete()


class MemberProfileElecteeFromNonMemberForm(ConvertNonMemberToMemberForm):
    class Meta:
        model = MemberProfile
        exclude = ('alum_mail_freq', 'edu_bckgrd_form', 'first_name',
                   'init_chapter', 'init_term', 'last_name',
                   'maiden_name', 'middle_name', 'nickname',
                   'standing', 'status', 'still_electing',
                   'suffix', 'title', 'uniqname', 'user')


class MemberProfileActiveFromNonMemberForm(ConvertNonMemberToMemberForm):
    class Meta:
        model = MemberProfile
        exclude = ('edu_bckgrd_form', 'first_name',
                   'last_name',
                   'maiden_name', 'middle_name', 'nickname',
                   'status', 'still_electing',
                   'suffix', 'title', 'uniqname', 'user')

                   
class ManageElecteeStillElectingForm(ModelForm):
    electee = forms.CharField(
                        widget=forms.TextInput(
                                attrs={
                                    'class': 'disabled',
                                    'readonly': 'readonly'
                                }
                        )
    )
    uniqname = forms.CharField(
                        widget=forms.TextInput(
                                attrs={
                                    'class': 'disabled',
                                    'readonly': 'readonly'
                                }
                        )
    )

    class Meta:
        model = MemberProfile
        fields = ['electee', 'uniqname', 'still_electing']

    def __init__(self, *args, **kwargs):
        super(ManageElecteeStillElectingForm, self).__init__(*args, **kwargs)
        if not self.instance:
            return
        self.fields['electee'].initial = self.instance.get_firstlast_name()

    def save(self, commit=True):
        uniqname = self.cleaned_data['uniqname']
        was_electing = MemberProfile.objects.get(
                                uniqname=uniqname).still_electing
        self.cleaned_data.pop('electee', None)
        instance = super(ManageElecteeStillElectingForm, self).save(
                                                        commit=commit)
        if was_electing and not instance.still_electing:
            electee_stopped_electing(instance)
        return instance


class BaseManageElecteeStillElectingFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseManageElecteeStillElectingFormSet,
              self).__init__(*args, **kwargs)

        #create filtering here whatever that suits you needs
        self.queryset = MemberProfile.objects.filter(
                            status__name='Electee').order_by(
                                                'last_name',
                                                'first_name',
                                                'uniqname')

ManageElecteeStillElectingFormSet = modelformset_factory(
                            MemberProfile,
                            form=ManageElecteeStillElectingForm,
                            formset=BaseManageElecteeStillElectingFormSet,
                            extra=0
)
