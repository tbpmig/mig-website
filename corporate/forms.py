from django import forms
from django.forms.formsets import BaseFormSet, formset_factory
from django.forms.models import modelformset_factory

from django_select2.forms import (
    Select2Widget
)
from localflavor.us.forms import USPhoneNumberField

from corporate.models import Company, MemberContact, NonMemberContact
from mig_main.models import MemberProfile, TBPChapter


class AddContactForm(forms.Form):
    address = forms.CharField(widget=forms.Textarea, required=False)
    company = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=Company.objects.order_by('name'),
                    label='Company',
    )
    gets_email = forms.BooleanField(required=False)
    has_contacted = forms.BooleanField(required=False)
    personal_contact_of = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=MemberProfile.get_members(),
                    label='Personal contact of',
                    required=False
    )
    member = forms.ModelChoiceField(
                    widget=Select2Widget( ),
                    queryset=MemberProfile.get_members(),
                    label='Contact',
                    required=False,
                    initial=None
    )

    speaking_interest = forms.BooleanField(required=False)
    name = forms.CharField(max_length=256, required=False)
    email = forms.EmailField(max_length=254, required=False)
    phone = USPhoneNumberField(required=False)
    short_bio = forms.CharField(widget=forms.Textarea, required=False)
    initiating_chapter = forms.ModelChoiceField(
                    widget=Select2Widget(),
                    queryset=TBPChapter.objects.order_by('state', 'letter'),
                    label='Initiating TBP Chapter (if any)',
                    required=False
    )

    id = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    is_member = forms.BooleanField(
                        widget=forms.HiddenInput(),
                        initial=None,
                        required=False
    )

    def __init__(self, *args, **kwargs):
        c = kwargs.pop('contact', None)
        ed = kwargs.pop('can_edit', False)
        super(AddContactForm, self).__init__(*args, **kwargs)
        if not ed:
            self.fields['gets_email'].widget = forms.HiddenInput()
        if c:
            self.fields['address'].initial = c.address
            self.fields['company'].initial = c.company
            self.fields['gets_email'].initial = c.gets_email
            self.fields['has_contacted'].initial = c.has_contacted
            self.fields['personal_contact_of'].initial = c.personal_contact_of
            self.fields['speaking_interest'].initial = c.speaking_interest
            self.fields['id'].initial = c.id
            if hasattr(c, 'member'):
                self.fields['is_member'].initial = True
                self.fields['member'].initial = c.member
            else:
                self.fields['is_member'].initial = None
                self.fields['member'].initial = None
                self.fields['name'].initial = c.name
                self.fields['email'].initial = c.email
                self.fields['phone'].initial = c.phone
                self.fields['short_bio'].initial = c.short_bio
                self.fields['initiating_chapter'].initial = c.initiating_chapter

    def clean(self):
        cleaned_data = super(AddContactForm, self).clean()
        member = cleaned_data.get('member')
        name = cleaned_data.get('name')

        if self.has_changed() and not(name or member):
            raise forms.ValidationError(
                            ('Either a member profile or a '
                             'contact name must be provided'))

    def is_overdetermined(self):
        if self.cleaned_data.get('member'):
            name = self.cleaned_data.get('name')
            email = self.cleaned_data.get('email')
            phone = self.cleaned_data.get('phone')
            bio = self.cleaned_data.get('short_bio')
            chapter = self.cleaned_data.get('initiating_chapter')
            if name or email or phone or bio or chapter:
                return True
        return False

    def save(self):
        if not self.has_changed():
            return
        id = self.cleaned_data.get('id')
        was_instance = id and id > 0
        was_member = self.cleaned_data.get('is_member')
        member = self.cleaned_data.get('member')
        if member:
            # save a MemberContact
            if was_instance and was_member:
                c = MemberContact.objects.get(id=id)
            else:
                c = MemberContact()
            if was_instance and not was_member:
                NonMemberContact.objects.filter(id=id).delete()
            c.member = member
        else:
            # save a NonMemberContact
            if was_instance and not was_member:
                c = NonMemberContact.objects.get(id=id)
            else:
                c = NonMemberContact()
            if was_instance and was_member:
                MemberContact.objects.filter(id=id).delete()
            c.name = self.cleaned_data.get('name')
            c.email = self.cleaned_data.get('email')
            c.phone = self.cleaned_data.get('phone')
            c.short_bio = self.cleaned_data.get('short_bio')
            c.initiating_chapter = self.cleaned_data.get('initiating_chapter')
        c.address = self.cleaned_data.get('address')
        c.company = self.cleaned_data.get('company')
        c.gets_email = self.cleaned_data.get('gets_email')
        c.has_contacted = self.cleaned_data.get('has_contacted')
        c.personal_contact_of = self.cleaned_data.get('personal_contact_of')
        c.speaking_interest = self.cleaned_data.get('speaking_interest')
        c.save()
        return c

    def delete(self):
        id = self.cleaned_data.get('id')
        was_instance = id and id > 0
        was_member = self.cleaned_data.get('is_member')
        if not was_instance:
            return
        if was_member:
            MemberContact.objects.filter(id=id).delete()
        else:
            NonMemberContact.objects.filter(id=id).delete()


class BaseContactFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', None)
        if initial:
            new_initial = []
            for contact in initial:
                tmp_dict = {}
                tmp_dict['id'] = contact.id
                tmp_dict['company'] = contact.company
                tmp_dict['gets_email'] = contact.gets_email
                tmp_dict['has_contacted'] = contact.has_contacted
                tmp_dict['address'] = contact.address
                tmp_dict['personal_contact_of'] = contact.personal_contact_of
                tmp_dict['speaking_interest'] = contact.speaking_interest
                if hasattr(contact, 'member'):
                    tmp_dict['is_member'] = True
                    tmp_dict['member'] = contact.member
                else:
                    tmp_dict['is_member'] = None
                    tmp_dict['member'] = None
                    tmp_dict['name'] = contact.name
                    tmp_dict['email'] = contact.email
                    tmp_dict['phone'] = contact.phone
                    tmp_dict['short_bio'] = contact.short_bio
                    tmp_dict['initiating_chapter'] = contact.initiating_chapter
                new_initial.append(tmp_dict)
            kwargs['initial'] = new_initial
        super(BaseContactFormSet, self).__init__(*args, **kwargs)

    def save(self):
        overdetermined = False
        for form in self.forms:
            if form.is_overdetermined():
                overdetermined = True
            if form.cleaned_data.get('DELETE'):
                form.delete()
            else:
                form.save()
        return overdetermined


ContactFormSet = formset_factory(
                        AddContactForm,
                        formset=BaseContactFormSet,
                        can_delete=True
)
