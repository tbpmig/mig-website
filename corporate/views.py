from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory, modelform_factory
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import RequestContext, loader

from corporate.auxiliary_scripts import update_resume_zips
from corporate.models import CorporateTextField, CorporateResourceGuide
from mig_main.utility import get_message_dict, Permissions


FORM_ERROR = 'Your submision contained errors, please correct and resubmit.'


def get_permissions(user):
    permission_dict = {'can_edit_corporate': Permissions.can_edit_corporate_page(user)}
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
