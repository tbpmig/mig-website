from datetime import date

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelform_factory,modelformset_factory
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.shortcuts import  get_object_or_404,redirect
from django.template import RequestContext, loader

from history.forms  import ArticleForm, WebArticleForm,ProjectDescriptionForm,ProjectPhotoFormset,BaseProjectReportHeaderForm
from history.models import WebsiteArticle, Publication,ProjectReportHeader,ProjectReport,CompiledProjectReport
from mig_main.models import AcademicTerm
from mig_main.utility import Permissions, get_previous_page,get_message_dict,get_previous_full_term
from event_cal.models import EventPhoto
def get_permissions(user):
    permission_dict={
        'can_post':Permissions.can_post_web_article(user),
        'can_edit':Permissions.can_approve_web_article(user),
        'post_button':Permissions.can_upload_articles(user),
        'is_member':hasattr(user,'userprofile') and user.userprofile.is_member(),
        'can_process_project_reports': Permissions.can_process_project_reports(user),
        }
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'main_nav':'publications',
        'new_bootstrap':True,
        'num_pending_stories':WebsiteArticle.objects.filter(approved=False).count(),

    })
    return context_dict
#This is not a url-findable method. To find article urls, use article_view
def get_article_view(request,article_id):
    request.session['current_page']=request.path
    today = date.today()
    web_articles    = WebsiteArticle.get_stories()
    if Permissions.can_post_web_article(request.user):
        NewArticleForm = modelform_factory(WebsiteArticle,form=WebArticleForm)
        if request.method == 'POST':
            form = NewArticleForm(request.POST)
            if form.is_valid():
                a=form.save()
                if Permissions.can_approve_web_article(request.user):
                    a.approved=True
                    a.save()
                    request.session['success_message']='Your webstory was posted successfully'
                else:
                    request.session['success_message']='Your webstory has been submitted and is awaiting approval'
                if hasattr(request.user,'userprofile') and request.user.userprofile.is_member():
                    a.created_by = request.user.userprofile.memberprofile
                    a.save()
                
                return get_previous_page(request, 'history:index')
            else:
                request.session['error_message']='There were errors in your submission. Please correct the noted errors.'
        else:
            form = NewArticleForm(initial={'date_posted':today})
    else:
        form = None
    template = loader.get_template('history/publications.html')
    if not article_id:
        if web_articles:
            article_id=web_articles[0].id
        else:
            article_id=0
    context_dict = {
        'web_articles':web_articles,
        'main_id':int(article_id),
        'form':form,
        'subnav':'news',
        'event_photos': (EventPhoto.objects.all() if form else None),
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def index(request):
    return get_article_view(request,None)
    
def edit_articles(request):
    if not Permissions.can_approve_web_article(request.user):
        request.session['error_message']='You are not authorized to edit web articles.'
        return redirect('history:index')
    prefix='webstories'
    WebStoryFormset = modelformset_factory(WebsiteArticle,can_delete=True)
    if request.method =='POST':
        formset = WebStoryFormset(request.POST,prefix=prefix,queryset = WebsiteArticle.objects.order_by('approved','-date_posted'))
        if formset.is_valid():
            formset.save()
            request.session['success_message']='Web stories updated successfully'
            return redirect('history:index')
        else:
            request.session['error_message']='Form is invalid. Please correct the noted errors.'
    else:
        formset = WebStoryFormset(prefix=prefix,queryset = WebsiteArticle.objects.order_by('approved','-date_posted'))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':prefix,
        'has_files':False,
        'can_add_row':False,
        'submit_name':'Update Website Stories',
        'form_title':'Edit Website Stories',
        'help_text':'Use this to edit or approve website stories submitted by others, for long stories, make sure to add the <fold> attribute.',
        'base':'history/base_history.html',
        'back_button':{'link':reverse('history:index'),'text':'To Website Stories'},
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def article_view(request,article_id):
    return get_article_view(request,article_id)

def get_printed_documents(request,document_type,document_name):
    request.session['current_page']=request.path
    today = date.today()
    documents   =Publication.objects.filter(type=document_type).order_by('date_published').exclude(date_published__gt=today)
    subnav='cornerstone'
    if document_type == 'AN':
        subnav='alumni_news'
    template = loader.get_template('history/printed_publications.html')
    context_dict = {
        'articles':documents,
        'page_title':document_name,
        'subnav':subnav,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def get_project_reports(request):
    if not hasattr(request.user,'userprofile')  or not request.user.userprofile.is_member():
        raise PermissionDenied()
    request.session['current_page']=request.path
    documents   =CompiledProjectReport.objects.filter(is_full=True).order_by('term')
    subnav='project_reports'
    template = loader.get_template('history/compiled_project_reports.html')
    context_dict = {
        'reports':documents,
        'page_title':'Compiled Project Reports from Past Semesters',
        'subnav':subnav,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def upload_article(request):
    if not Permissions.can_upload_articles(request.user):
        raise PermissionDenied()
    if request.method == 'POST':
        form = ArticleForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            request.session['success_message']='Article uploaded successfully'
            return get_previous_page(request,'history:cornerstone_view')
        else:
            request.session['error_message']='There were errors in your submission. Please correct the noted errors.'
    else:
        form = ArticleForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'cornerstone',
        'has_files':True,
        'submit_name':'Upload Printed Publication',
        'form_title':'Upload Article',
        'help_text':'Make sure to specify the type of publication.',
        'base':'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
            

def cornerstone_view(request):
    return get_printed_documents(request,'CS','The Cornerstone')

def alumninews_view(request):
    return get_printed_documents(request,'AN','Alumni Newsletter')

def process_project_report_compilation(request):
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    current_term = AcademicTerm.get_current_term()
    if current_term.semester_type.name=='Summer':
        #Likely the whole one
        winter_term = get_previous_full_term(current_term)
        fall_term = None
    elif current_term.semester_type.name=='Fall':
        #either because summer term may be skipped to ease book keeping
        winter_term = get_previous_full_term(current_term)
        fall_term = current_term
    else:
        #could conceivably be either
        winter_term = current_term
        fall_term = get_previous_full_term(current_term)

    pr_fall=None
    pr_winter=None
    if fall_term:
        prs=ProjectReportHeader.objects.filter(terms=fall_term).distinct()
        if prs.exists():
            pr_fall=prs[0]

    if winter_term:
        prs=ProjectReportHeader.objects.filter(terms=winter_term).distinct()
        if prs.exists():
            pr_winter=prs[0]
    template = loader.get_template('history/project_report_compilation_manager.html')
    context_dict = {
        'fall_term':fall_term,
        'winter_term':winter_term,
        'pr_fall':pr_fall,
        'pr_winter':pr_winter,
        'subnav':'project_reports',
        'base':'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def start_project_report_compilation(request,term_id):
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    term = get_object_or_404(AcademicTerm,id=term_id)
    ProjectForm =modelform_factory(ProjectReportHeader,form=BaseProjectReportHeaderForm)
    pr = ProjectReportHeader.objects.filter(terms=term).distinct()
    if request.method=='POST':
        if pr.exists():
            form = ProjectForm(request.POST,instance=pr.all()[0])
        else:
            form = ProjectForm(request.POST)
        if form.is_valid():
            instance=form.save()
            request.session['success_message'] = 'Project report metadata/header created/updates'
            return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message']='There were errors in your submission. Please correct'
    else:
        if pr.exists():
            form = ProjectForm(instance=pr.all()[0])
        else:
            form = ProjectForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'project_reports',
        'has_files':False,
        'submit_name':'Confirm Meta Data',
        'form_title':'Create Project Reports',
        'help_text':'This will begin the process of assembling the project reports.',
        'base':'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def process_project_reports(request,prh_id,pr_id):
    # double check permissions
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    pr_header = get_object_or_404(ProjectReportHeader,id=prh_id)
    reports = pr_header.get_project_reports().order_by('target_audience','planning_start_date')
    #
    if int(pr_id) == 0:
        # get started
        pr=reports[0]
        next_index = 1
    else:
        #process the current report
        pr = get_object_or_404(ProjectReport,id=pr_id)
        for index,item in enumerate(reports):
            if item==pr:
                next_index =index+1
                break
    if request.method=='POST':
        form = ProjectDescriptionForm(request.POST)
        if form.is_valid():
            request.session['success_message'] = 'Descriptions updated'
            pr.set_description(form.cleaned_data['description'])
            if next_index< reports.count():
                pr_header.last_processed=reports[next_index].id
                pr_header.save()
                return redirect('history:process_project_reports',pr_header.id,reports[next_index].id)
            else:
                pr_header.finished_processing=True
                pr_header.save()
                return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message']='Submission Error(s). Please correct'
    else:
        form = ProjectDescriptionForm(initial={'description':pr.get_descriptions()})
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'project_reports',
        'has_files':False,
        'submit_name':'Confirm Project Description: '+pr.name,
        'form_title':'Create Project Reports: Project Descriptions',
        'help_text':'This is step 2 of 4. Please make updates to the project descriptions as necessary. A suggested description based on project leader submissions is pre-loaded below for:\nProject Name: %s\nTerm: %s\nCategory: %s\nPlanning Start: %s\nProject %d out of %d'%(pr.name,unicode(pr.term),pr.get_target_audience_display(),pr.planning_start_date,next_index,reports.count()),
        'base':'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def process_project_report_photos(request,prh_id,pr_id):
    # double check permissions

    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    pr_header = get_object_or_404(ProjectReportHeader,id=prh_id)
    reports = pr_header.get_project_reports().order_by('target_audience','planning_start_date')
    #
    if int(pr_id) == 0:
        # get started
        pr=reports[0]
        next_index = 1
    else:
        #process the current report
        pr = get_object_or_404(ProjectReport,id=pr_id)
        for index,item in enumerate(reports):
            if item==pr:
                next_index =index+1
                break
    photo_query = EventPhoto.objects.filter((Q(event__project_report = pr)&Q(project_report=None))|Q(project_report=pr))
    needs_redirect = False
    while not photo_query.exists():
        needs_redirect=True
        if next_index< reports.count():
            pr = reports[next_index]
            next_index +=1
            photo_query = EventPhoto.objects.filter((Q(event__project_report = pr)&Q(project_report=None))|Q(project_report=pr))
        else:
            pr_header.finished_photos=True
            pr_header.save()
            return redirect('history:process_project_report_compilation')
    if needs_redirect:
        pr_header.last_photo=pr.id
        pr_header.save()
        return redirect('history:process_project_report_photos',pr_header.id,pr.id)

    if request.method=='POST':
        formset = ProjectPhotoFormset(request.POST,request.FILES,queryset=photo_query)
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = 'Photos updated'
            if next_index< reports.count():
                pr_header.last_photo=reports[next_index].id
                pr_header.save()
                return redirect('history:process_project_report_photos',pr_header.id,reports[next_index].id)
            else:
                pr_header.finished_photos=True
                pr_header.save()
                return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message']='Submission Error(s). Please correct'
    else:
        formset = ProjectPhotoFormset(queryset=photo_query)
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'project_reports',
        'has_files':True,
        'submit_name':'Confirm Photos: '+pr.name,
        'can_add':True,
        'form_title':'Create Project Reports: Project Photos',
        'help_text':'This is step 3 of 4. Please make updates to the project descriptions as necessary. A suggested description based on project leader submissions is pre-loaded below for:\nProject Name: %s\nTerm: %s\nCategory: %s\nPlanning Start: %s\nProject %d out of %d'%(pr.name,unicode(pr.term),pr.get_target_audience_display(),pr.planning_start_date,next_index,reports.count()),
        'base':'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def compile_project_reports(request,prh_id):
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    prh = get_object_or_404(ProjectReportHeader,id=prh_id)
    prh.write_tex_files()
    return redirect('history:process_project_report_compilation')
