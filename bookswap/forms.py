from django import forms
from django.core.validators import RegexValidator
from django.forms import ModelForm, Form, ValidationError
from django.utils.translation import ugettext as _

from bookswap.models import BookSwapPerson


class StartTransactionForm(Form):
    user_UMID = forms.CharField(required=False)
    user_uniqname = forms.CharField(required=False)
    user_barcode = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(StartTransactionForm, self).clean()
        has_UMID = cleaned_data.get('user_UMID')
        has_uniqname = cleaned_data.get('user_uniqname')
        has_barcode = cleaned_data.get('user_barcode')
        error_list = []
        if not (has_UMID or has_uniqname or has_barcode):
            error_list.append(
                        ValidationError(_('You must provide at '
                                          'least one query'))
            )
        if error_list:
            raise ValidationError(error_list)
        return cleaned_data

    def get_user(self):
        if not hasattr(self,'cleaned_data'):
            raise ValidationError('Form not yet validated')
        cleaned_data = self.cleaned_data
        UMID = cleaned_data.get('user_UMID')
        uniqname = cleaned_data.get('user_uniqname')
        barcode = cleaned_data.get('user_barcode')
        if barcode:
            bsp = BookSwapPerson.objects.filter(barcode=barcode)
            if bsp.exists():
                return bsp[0]
        if uniqname:
            bsp = BookSwapPerson.objects.filter(user_profile__uniqname=uniqname)
            if bsp.exists():
                return bsp[0]
        if UMID:
            bsp = BookSwapPerson.objects.filter(UMID=UMID)
            if bsp.exists():
                return bsp[0]
        return None


class BookSwapPersonForm(ModelForm):
    """ This version is for updating or if they already have a UserProfile."""
    class Meta:
        model = BookSwapPerson
        exclude = ['user_profile']


class BookSwapPersonFormNoProfile(ModelForm):
    """ This version is for if they had no profile found."""
    first_name = forms.CharField(max_length=40)
    last_name = forms.CharField(max_length=40)
    uniqname = forms.CharField(
                 max_length=8,
                 validators=[RegexValidator(
                               regex=r'^[a-z]{3,8}$',
                               message=('Your uniqname must be 3-8 characters,'
                                        'all lowercase.')
                            )
                            ]
    )
    class Meta:
        model = BookSwapPerson
        exclude = ['user_profile']
    def clean(self):
        cleaned_data = super(BookSwapPersonFormNoProfile, self).clean()
        m = MemberProfile.objects.filter(uniqname=cleaned_data.get('uniqname'))
        if m.exists():
            UMID = cleaned_data.get('UMID')
            if m.UMID != UMID:
                raise ValidationError(_('UMID does not match that in system'))
        return cleaned_data
        
    def save(self, commit=True):
        bsp = super(BookSwapPersonFormNoProfile,self).save(commit=False)
        uniqname = self.cleaned_data.get('uniqname')
        user_profile = UserProfile.objects.filter(uniqname=uniqname)
        if not user_profile.exists():
            users_w_name = User.objects.filter(username=uniqname)
            first_name = self.cleaned_data.get('first_name')
            last_name = self.cleaned_data.get('last_name')
            if not users_w_name.exists():
                user = User.objects.create_user(user_name, user_name+'@umich.edu', '')
            else:
                user = users_w_name[0]
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            user.save()
            user_profile = UserProfile()
            user_profile.uniqname = uniqname
            user_profile.first_name = first_name
            user_profile.last_name = last_name
            
        