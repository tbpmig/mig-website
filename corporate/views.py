from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory, modelform_factory
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django_ajax.decorators import ajax
from corporate.auxiliary_scripts import update_resume_zips
from corporate.forms import AddContactForm,ContactFormSet
from corporate.models import CorporateTextField, CorporateResourceGuide
from corporate.models import CompanyContact, Company, JobField, CorporateEmail
from mig_main.utility import get_message_dict, Permissions

FORM_ERROR = 'Your submision contained errors, please correct and resubmit.'


def get_permissions(user):
    permission_dict = {
        'can_edit_corporate': Permissions.can_edit_corporate_page(user),
        'can_add_contact': Permissions.can_add_corporate_contact(user),
        'can_edit_contacts': Permissions.can_edit_corporate_page(user),
        'can_add_company': Permissions.can_add_company(user),
    }
    return permission_dict


def get_common_context(request):
    context_dict = get_message_dict(request)
    contact_text = CorporateTextField.objects.filter(section='CT')
    context_dict.update({
        'request': request,
        'contact_text': contact_text,
        'main_nav': 'corporate',
        })
    return context_dict


def index(request):
    request.session['current_page'] = request.path
    template = loader.get_template('corporate/corporate.html')
    involvement_text = CorporateTextField.objects.filter(section='OP')
    context_dict = {
        'involvement_text': involvement_text,
        'subnav': 'index',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def resumes(request):
    request.session['current_page'] = request.path
    template = loader.get_template('corporate/resume_book.html')
    context_dict = {
        'by_major_zip': 'TBP_resumes_by_major.zip',
        'by_year_zip': 'TBP_resumes_by_year.zip',
        'subnav': 'resumes',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def update_corporate_page(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to edit the corporate page'
        return redirect('corporate:index')
    prefix = 'corporate_page'
    CorporateTextForm = modelformset_factory(CorporateTextField,
                                             extra=1, exclude=[])
    formset = CorporateTextForm(request.POST or None,prefix=prefix)
    if request.method == 'POST':
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message'] = 'Corporate page successfully updated.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR
    context_dict = {
        'formset': formset,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Update Corporate Page',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Edit Corporate Page Text',
        'help_text': ('The text shown on the corporate main page. This text '
                      'uses markdown syntax.'),
        'can_add_row': False,
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context))


def update_resource_guide(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to edit the corporate page'
        return redirect('corporate:index')
    ResourceGuideForm = modelform_factory(CorporateResourceGuide, exclude=('active',))
    if request.method == 'POST':
        form = ResourceGuideForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            previously_active_guides = CorporateResourceGuide.objects.filter(active=True)
            for guide in previously_active_guides:
                guide.active = False
                guide.save()
            instance.active = True
            instance.save()
            update_resume_zips()
            request.session['success_message'] = 'Corporate resource guide successfully updated.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR
    else:
        form = ResourceGuideForm()
    context_dict = {
        'form': form,
        'subnav': 'index',
        'has_files': True,
        'submit_name': 'Update Corporate Resource Guide',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Edit Corporate Resource Guide',
        'help_text': ('This guide is inluded in the resume zip files. Update '
                      'it when the information (or the officer) changes.'),
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))


def add_company_contact(request):
    if not Permissions.can_add_corporate_contact(request.user):
        request.session['error_message'] = 'You are not authorized to add company contacts'
        return redirect('corporate:index')
    prefix = 'corporate_page'
    can_edit = Permissions.can_edit_corporate_page(request.user)
    form = AddContactForm(request.POST or None,prefix=prefix,can_edit=can_edit)
    if request.method == 'POST':
        if form.is_valid():
            if form.is_overdetermined():
                request.session['warning_message'] = 'Name, email, phone, bio, and chapter are ignored when profile provided.'  
            instance = form.save()
            request.session['success_message'] = 'Corporate contact successfully added.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR
    help_text = 'Add a contact to the company contacts database.'
    if not can_edit:
        help_text = help_text + (' Note: you are adding a suggested contact; '
                                 'they will not be emailed unless approved by '
                                 'the Corporate Relations Officer.')
    context_dict = {
        'form': form,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Add company contact',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Add company contact',
        'help_text': help_text,
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))

def edit_company_contacts(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to add company contacts'
        return redirect('corporate:index')
    prefix = 'corporate_page'

    formset = ContactFormSet(request.POST or None,prefix=prefix,initial=CompanyContact.get_contacts())
    if request.method == 'POST':
        if formset.is_valid():
            overdetermined = formset.save()
            if overdetermined:
                request.session['warning_message'] = 'Name, email, phone, bio, and chapter are ignored when profile provided.'  
            request.session['success_message'] = 'Corporate contact successfully added.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR
    context_dict = {
        'formset': formset,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Update company contacts',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Edit company contacts',
        'help_text': ('Edit the list of company contacts. '
                      'Contact info is ignored if a profile is provided.'),
        'can_add_row':True,
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context))


def add_company(request):
    if not Permissions.can_add_company(request.user):
        request.session['error_message'] = 'You are not authorized to add companies'
        return redirect('corporate:index')
    prefix = 'corporate_page'
    AddCompanyForm = modelform_factory(Company)
    form = AddCompanyForm(request.POST or None,prefix=prefix)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            request.session['success_message'] = 'Company successfully added.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR

    context_dict = {
        'form': form,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Add company',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Add company',
        'help_text': ('Add company information. If the appropriate industry '
                      'is not present, you need to add that first'),
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))


def add_jobfield(request):
    if not Permissions.can_add_company(request.user):
        request.session['error_message'] = 'You are not authorized to add industries'
        return redirect('corporate:index')
    prefix = 'corporate_page'
    AddIndustryForm = modelform_factory(JobField)
    form = AddIndustryForm(request.POST or None,prefix=prefix)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            request.session['success_message'] = 'Industry successfully added.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR

    context_dict = {
        'form': form,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Add industry',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Add industry',
        'help_text': ('Add industry information. Select all relevant majors.'),
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))


def view_company_contacts(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to view company contacts'
        return redirect('corporate:index')
   
    context_dict = {
        'contacts': CompanyContact.get_contacts(),
        'subnav': 'index',
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('corporate/contacts_table.html')
    return HttpResponse(template.render(context))


def view_and_send_email(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to email companies'
        return redirect('corporate:index')
    existing_email = CorporateEmail.objects.filter(active=True)
    if existing_email.exists():
        existing_email = existing_email[0]
    else:
        request.session['error_message'] = 'No email specified'
        return redirect('corporate:index')
    contacts = CompanyContact.get_contacts(gets_email=True)
    context_dict = {
        'contacts': contacts,
        'email':existing_email.preview_email(),
        'mig_alum_email':existing_email.preview_email(mig_alum=True),
        'other_alum_email':existing_email.preview_email(other_alum=True),
        'previous_contact_email':existing_email.preview_email(previous_contact=True),
        'personal_contact_email':existing_email.preview_email(personal_contact=True),
        'subnav': 'index',
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('corporate/view_and_send_email.html')
    return HttpResponse(template.render(context))

@ajax
def send_corporate_email(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to email companies'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>'''%(request.session.pop('error_message'))}}
    existing_email = CorporateEmail.objects.filter(active=True)
    if existing_email.exists():
        existing_email[0].send_corporate_email()
        request.session['success_message']='Companies successfully emailed'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Success:</strong>%s</div>'''%(request.session.pop('success_message'))}}
    else:
        request.session['error_message'] = 'Company email text does not exist'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong>%s</div>'''%(request.session.pop('error_message'))}}

def update_corporate_email(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message'] = 'You are not authorized to email companies'
        return redirect('corporate:index')
    prefix = 'corporate_email'
    existing_email = CorporateEmail.objects.filter(active=True)
    UpdateEmailForm = modelform_factory(CorporateEmail)
    if existing_email.exists():
        form = UpdateEmailForm(request.POST or None,prefix=prefix,instance=existing_email[0])
    else:
        form = UpdateEmailForm(request.POST or None,prefix=prefix)
        
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            instance.id=None
            instance.pk=None
            instance.save()
            if existing_email.exists():
                ex=existing_email[0]
                ex.active=False
                ex.save()
            request.session['success_message'] = 'Company email successfully updated.'
            return redirect('corporate:index')
        else:
            request.session['error_message'] = FORM_ERROR

    context_dict = {
        'form': form,
        'subnav': 'index',
        'prefix': prefix,
        'has_files': False,
        'submit_name': 'Update corporate email',
        'back_button': {'link': reverse('corporate:index'),
                        'text': 'To Corporate Page'},
        'form_title': 'Update corporate email',
        'help_text': ('Update the email sent to companies to encourage their'
                      'participation in TBP corporate events.\n\nUse '
                      '{{company_name}} in the subject line as a placeholder'
                      'and {{extra_text}} in the body as a placeholder for the'
                      'extra text to members or personal contacts.'),
        'base': 'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))