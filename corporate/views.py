import os
import zipfile
import shutil
import time

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelformset_factory,modelform_factory
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.template.defaultfilters import slugify

from corporate.models import CorporateTextField,CorporateResourceGuide
from migweb.settings import PROJECT_PATH, MEDIA_ROOT
from mig_main.models import Major, MemberProfile, Standing,get_members
from mig_main.utility import get_message_dict,Permissions

RESUMES_BY_MAJOR_LOCATION = os.path.sep.join([MEDIA_ROOT,'Resumes_by_major'])
RESUMES_BY_YEAR_LOCATION = os.path.sep.join([MEDIA_ROOT,'Resumes_by_year'])

def get_permissions(user):
    permission_dict={'can_edit_corporate':Permissions.can_edit_corporate_page(user)}
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    contact_text = CorporateTextField.objects.filter(section='CT')
    context_dict.update({
        'request':request,
        'contact_text':contact_text,
        })
    return context_dict
def zipdir(path,zipf):
    for root,dirs,files in os.walk(path):
        for f in files:
            zipf.write(os.path.join(root,f))

def compile_resumes():
    shutil.rmtree(RESUMES_BY_MAJOR_LOCATION)
    os.makedirs(RESUMES_BY_MAJOR_LOCATION)
    resource_guides = CorporateResourceGuide.objects.filter(active=True)
    if resource_guides:
        shutil.copy(PROJECT_PATH+resource_guides[0].resource_guide.url,os.path.sep.join([RESUMES_BY_MAJOR_LOCATION,slugify(resource_guides[0].name)+'.pdf']))
    for resume_major in Major.objects.all():
        query=Q(major=resume_major)
        users_in_major = get_members().filter(query)
        for user in users_in_major:
            if user.resume:
                major_dir = os.path.sep.join([RESUMES_BY_MAJOR_LOCATION,slugify(resume_major.name)])
                if not os.path.exists(major_dir):
                    os.makedirs(major_dir)
                resume_name=slugify(user.last_name+'_'+user.first_name+'_'+user.uniqname)+'.pdf'
                shutil.copy(PROJECT_PATH+user.resume.url,os.path.sep.join([major_dir,resume_name]))
    if os.path.exists(RESUMES_BY_YEAR_LOCATION):
        shutil.rmtree(RESUMES_BY_YEAR_LOCATION)
    os.makedirs(RESUMES_BY_YEAR_LOCATION)
    if resource_guides:
        shutil.copy(PROJECT_PATH+resource_guides[0].resource_guide.url,os.path.sep.join([RESUMES_BY_YEAR_LOCATION,slugify(resource_guides[0].name)+'.pdf']))
    not_alum = ~Q(name='Alumni')
    for standing in Standing.objects.all():
        members = get_members().filter(standing=standing)
        if standing.name == 'Alumni':
            status_dir = os.path.sep.join([RESUMES_BY_YEAR_LOCATION,slugify(standing.name)])
        else:
            status_dir = os.path.sep.join([RESUMES_BY_YEAR_LOCATION, slugify(standing.name)+'-student'])
        if not os.path.exists(status_dir):
            os.makedirs(status_dir)
        for user in members:
            if user.resume:
                current_grad_year = user.expect_grad_date.year
                year_dir = os.path.sep.join([status_dir,'Graduating'+slugify(current_grad_year)])
                if not os.path.exists(year_dir):
                    os.makedirs(year_dir)
                resume_name=slugify(user.last_name+'_'+user.first_name+'_'+user.uniqname)+'.pdf'
                shutil.copy(PROJECT_PATH+user.resume.url,os.path.sep.join([year_dir,resume_name]))
            
def update_resume_zips():
    compile_resumes()
    current_path = os.getcwd()
    zip_file_name = os.sep.join([MEDIA_ROOT,'TBP_resumes_by_major.zip'])
    try:
        os.remove(zip_file_name)
    except OSError:
        pass
    zip_f = zipfile.ZipFile(zip_file_name,'w')
    os.chdir(RESUMES_BY_MAJOR_LOCATION)
    zipdir('.',zip_f)
    zip_f.close()
    zip_file_name_year = os.sep.join([MEDIA_ROOT,'TBP_resumes_by_year.zip'])
    try:
        os.remove(zip_file_name_year)
    except OSError:
        pass
    zip_f = zipfile.ZipFile(zip_file_name_year,'w')
    os.chdir(RESUMES_BY_YEAR_LOCATION)
    zipdir('.',zip_f)
    zip_f.close()
    os.chdir(current_path)

def index(request):
    request.session['current_page']=request.path
    template = loader.get_template('corporate/corporate.html')
    involvement_text = CorporateTextField.objects.filter(section='OP')
    context_dict = {
        'involvement_text':involvement_text,
        'subnav':'index',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def resumes(request):
    request.session['current_page']=request.path
    template = loader.get_template('corporate/resume_book.html')
    context_dict = {
        'by_major_zip':'TBP_resumes_by_major.zip',
        'by_year_zip':'TBP_resumes_by_year.zip',
        'subnav':'resumes',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
#    
def update_corporate_page(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message']='You are not authorized to edit the corporate page'
        return redirect('corporate:index')
    CorporateTextForm = modelformset_factory(CorporateTextField,extra=1)
    if request.method=='POST':
        formset = CorporateTextForm(request.POST)
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message']='Corporate page successfully updated.'
            return redirect('corporate:index')
        else:
            request.session['error_message']='Your submision contained errors, please correct and resubmit.'
    else:
       formset=CorporateTextForm()
    context_dict = {
        'formset':formset,
        'subnav':'index',
        'has_files':False,
        'submit_name':'Update Corporate Page',
        'back_button':{'link':reverse('corporate:index'),'text':'To Corporate Page'},
        'form_title':'Edit Corporate Page Text',
        'help_text':'The text shown on the corporate main page. This text uses markdown syntax.',
        'can_add_row':False,
        'base':'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context))

def update_resource_guide(request):
    if not Permissions.can_edit_corporate_page(request.user):
        request.session['error_message']='You are not authorized to edit the corporate page'
        return redirect('corporate:index')
    ResourceGuideForm = modelform_factory(CorporateResourceGuide,exclude=('active',))
    if request.method=='POST':
        form = ResourceGuideForm(request.POST,request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            previously_active_guides = CorporateResourceGuide.objects.filter(active=True)
            for guide in previously_active_guides:
                guide.active=False
                guide.save()
            instance.active = True
            instance.save()
            update_resume_zips()
            request.session['success_message']='Corporate resource guide successfully updated.'
            return redirect('corporate:index')
        else:
            request.session['error_message']='Your submision contained errors, please correct and resubmit.'
    else:
       form=ResourceGuideForm()
    context_dict = {
        'form':form,
        'subnav':'index',
        'has_files':True,
        'submit_name':'Update Corporate Resource Guide',
        'back_button':{'link':reverse('corporate:index'),'text':'To Corporate Page'},
        'form_title':'Edit Corporate Resource Guide',
        'help_text':'This guide is inluded in the resume zip files. Update it when the information (or the officer) changes.',
        'base':'corporate/base_corporate.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))
