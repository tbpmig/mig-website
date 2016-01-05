from datetime import date

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelform_factory, modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template import RequestContext, loader

from history.forms import (
            ArticleForm,
            WebArticleForm,
            ProjectDescriptionForm,
            ProjectPhotoFormset,
            BaseProjectReportHeaderForm,
)
from history.models import (
            WebsiteArticle,
            Publication,
            ProjectReportHeader,
            ProjectReport,
            CompiledProjectReport,
)
from mig_main import messages
from mig_main.models import AcademicTerm
from mig_main.utility import (
            Permissions,
            get_previous_page,
            get_message_dict,
            get_previous_full_term,
)
from event_cal.models import EventPhoto


def get_permissions(user):
    can_process_reports = Permissions.can_process_project_reports(user)
    permission_dict = {
        'can_post': Permissions.can_post_web_article(user),
        'can_edit': Permissions.can_approve_web_article(user),
        'post_button': Permissions.can_upload_articles(user),
        'is_member': (hasattr(user, 'userprofile') and
                      user.userprofile.is_member()),
        'can_process_project_reports': can_process_reports,
    }
    return permission_dict


def get_common_context(request):
    context_dict = get_message_dict(request)
    pending_stories = WebsiteArticle.objects.filter(approved=False)
    context_dict.update({
        'request': request,
        'main_nav': 'publications',
        'new_bootstrap': True,
        'num_pending_stories': pending_stories.count(),
    })
    return context_dict


def get_article_view(request, article_id):
    """ The helper view method for the index and the article view.

    This is not a url-findable method. To find article urls, use article_view.
    This also serves a form to submit new articles, provided that the user
    has the permissions to submit such a story.
    """
    request.session['current_page'] = request.path
    today = date.today()
    web_articles = WebsiteArticle.get_stories()
    if (hasattr(request.user, 'userprofile') and
       request.user.userprofile.is_member()):
        profile = request.user.userprofile.memberprofile
    else:
        profile = None
    can_post = Permissions.can_post_web_article(request.user)
    NewArticleForm = modelform_factory(WebsiteArticle, form=WebArticleForm)
    form = NewArticleForm(request.POST or None,
                          initial={'date_posted': today})
    if can_post and request.method == 'POST':
        if form.is_valid():
            a = form.save()
            if Permissions.can_approve_web_article(request.user):
                a.approved = True
                a.save()
                request.session['success_message'] = ('Your webstory was '
                                                      'posted')
            else:
                request.session['success_message'] = ('Your webstory has '
                                                      'been submitted and '
                                                      'is awaiting '
                                                      'approval')
            if profile:
                a.created_by = profile
                a.save()
            tweet_option = form.cleaned_data.pop('tweet_option', 'N')
            if tweet_option == 'T':
                a.tweet_story(False)
            elif tweet_option == 'H':
                a.tweet_story(True)
            return get_previous_page(request, 'history:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    elif not can_post:
        form = None
    template = loader.get_template('history/publications.html')
    if not article_id:
        if web_articles:
            article_id = web_articles[0].id
        else:
            article_id = 0
    context_dict = {
        'web_articles': web_articles,
        'main_id': int(article_id),
        'form': form,
        'subnav': 'news',
        'event_photos': (EventPhoto.objects.all() if form else None),
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def index(request):
    """ Shows the article view for the first article.
    """
    return get_article_view(request, None)


def edit_articles(request):
    """ Allows editing and approving articles."""
    if not Permissions.can_approve_web_article(request.user):
        request.session['error_message'] = ('You are not authorized to edit '
                                            'web articles.')
        return redirect('history:index')
    prefix = 'webstories'
    WebStoryFormset = modelformset_factory(WebsiteArticle, can_delete=True)
    formset = WebStoryFormset(
                request.POST or None,
                prefix=prefix,
                queryset=WebsiteArticle.objects.order_by(
                                            'approved',
                                            '-date_posted'
                )
    )
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = ('Web stories updated '
                                                  'successfully')
            return redirect('history:index')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset': formset,
        'prefix': prefix,
        'has_files': False,
        'can_add_row': False,
        'submit_name': 'Update Website Stories',
        'form_title': 'Edit Website Stories',
        'help_text': ('Use this to edit or approve website stories '
                      'submitted by others, for long stories, make sure to '
                      'add the <fold> attribute.'),
        'base': 'history/base_history.html',
        'back_button': {
                'link': reverse('history:index'),
                'text': 'To Website Stories'
        },
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def article_view(request, article_id):
    """ The article view for a particular article."""
    return get_article_view(request, article_id)


def get_printed_documents(request, document_type, document_name):
    """ Helper function for accessing Alumni Newsletters or Cornerstones.
    """
    request.session['current_page'] = request.path
    documents = Publication.get_published(document_type)
    subnav = 'cornerstone'
    if document_type == 'AN':
        subnav = 'alumni_news'
    template = loader.get_template('history/printed_publications.html')
    context_dict = {
        'articles': documents,
        'page_title': document_name,
        'subnav': subnav,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def get_project_reports(request):
    """ View to retrieve the compiled project reports.
    """
    if (not hasattr(request.user, 'userprofile') or
       not request.user.userprofile.is_member()):
        raise PermissionDenied()
    request.session['current_page'] = request.path
    documents = CompiledProjectReport.objects.filter(
                        is_full=True
    ).order_by('term')
    subnav = 'project_reports'
    template = loader.get_template('history/compiled_project_reports.html')
    context_dict = {
        'reports': documents,
        'page_title': 'Compiled Project Reports from Past Semesters',
        'subnav': subnav,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def upload_article(request):
    """ Upload a printed article """
    if not Permissions.can_upload_articles(request.user):
        raise PermissionDenied()
    form = ArticleForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            request.session['success_message'] = ('Article uploaded '
                                                  'successfully')
            return get_previous_page(request, 'history:cornerstone_view')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'cornerstone',
        'has_files': True,
        'submit_name': 'Upload Printed Publication',
        'form_title': 'Upload Article',
        'help_text': 'Make sure to specify the type of publication.',
        'base': 'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def cornerstone_view(request):
    """ Shows the page witht he list of Cornerstones."""
    return get_printed_documents(request, 'CS', 'The Cornerstone')


def alumninews_view(request):
    """ Shows the page with the list of Alumni Newsletters."""
    return get_printed_documents(request, 'AN', 'Alumni Newsletter')


def process_project_report_compilation(request):
    """ Starts or resumes the process of compiling project reports.

    Basically the landing page for further action.
    """
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    current_term = AcademicTerm.get_current_term()
    if current_term.semester_type.name == 'Summer':
        # Likely the whole one
        winter_term = get_previous_full_term(current_term)
        fall_term = None
    elif current_term.semester_type.name == 'Fall':
        # either because summer term may be skipped to ease book keeping
        winter_term = get_previous_full_term(current_term)
        fall_term = current_term
    else:
        # could conceivably be either
        winter_term = current_term
        fall_term = get_previous_full_term(current_term)

    pr_fall = None
    pr_winter = None
    if fall_term:
        prs = ProjectReportHeader.objects.filter(terms=fall_term).distinct()
        if prs.exists():
            pr_fall = prs[0]

    if winter_term:
        prs = ProjectReportHeader.objects.filter(terms=winter_term).distinct()
        if prs.exists():
            pr_winter = prs[0]
    template = loader.get_template(
                    'history/project_report_compilation_manager.html'
    )
    context_dict = {
        'fall_term': fall_term,
        'winter_term': winter_term,
        'pr_fall': pr_fall,
        'pr_winter': pr_winter,
        'subnav': 'project_reports',
        'base': 'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def start_project_report_compilation(request, term_id):
    """ The page visited once the button is clicked to start compiling
    the reports.
    """
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    term = get_object_or_404(AcademicTerm, id=term_id)
    ProjectForm = modelform_factory(
                        ProjectReportHeader,
                        form=BaseProjectReportHeaderForm
    )
    prs = ProjectReportHeader.objects.filter(terms=term).distinct()
    if prs.exists():
        pr = prs[0]
    else:
        pr = ProjectReportHeader()
    form = ProjectForm(request.POST or None, instance=pr)
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save()
            request.session['success_message'] = ('Project report metadata/'
                                                  'header created/updated')
            return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form': form,
        'subnav': 'project_reports',
        'has_files': False,
        'submit_name': 'Confirm Meta Data',
        'form_title': 'Create Project Reports',
        'help_text': ('This will begin the process of assembling the '
                      'project reports.'),
        'base': 'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def process_project_reports(request, prh_id, pr_id):
    """ Processing the project report given by pr_id.

    If pr_id is zero then this starts at the beginning (a very fine place
    to start). This pulls all the descriptions for events or non-even-projects
    associated with the project report and has the user consolidate them into
    one.
    """
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    pr_header = get_object_or_404(ProjectReportHeader, id=prh_id)
    reports = pr_header.get_project_reports().order_by(
                                        'target_audience',
                                        'planning_start_date',
                                        'id',
    )

    if int(pr_id) == 0:
        # get started
        pr = reports[0]
        next_index = 1
    else:
        # process the current report
        pr = get_object_or_404(ProjectReport, id=pr_id)
    form = ProjectDescriptionForm(
                        request.POST or None,
                        initial={'description': pr.get_descriptions()},
    )
    if request.method == 'POST':
        if form.is_valid():
            request.session['success_message'] = 'Descriptions updated'
            pr.set_description(form.cleaned_data['description'])
            # determine which report would be the next one to process
            # (for redirection sake)
            for index, item in enumerate(reports):
                if item == pr:
                    next_index = index+1
                    break
            if next_index < reports.count():
                pr_header.last_processed = reports[next_index].id
                pr_header.save()
                return redirect('history:process_project_reports',
                                pr_header.id,
                                reports[next_index].id)
            else:
                pr_header.finished_processing = True
                pr_header.save()
                return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_form.html')
    help_text = ('This is step 2 of 4. Please make updates to the '
                 'project descriptions as necessary. A suggested '
                 'description based on project leader submissions is '
                 'pre-loaded below for:\nProject Name: %s\nTerm: '
                 '%s\nCategory: %s\nPlanning Start: %s\nProject %d out '
                 'of %d') % (pr.name,
                             unicode(pr.term),
                             pr.get_target_audience_display(),
                             pr.planning_start_date,
                             next_index,
                             reports.count())
    context_dict = {
        'form': form,
        'subnav': 'project_reports',
        'has_files': False,
        'submit_name': 'Confirm Project Description: '+pr.name,
        'form_title': 'Create Project Reports: Project Descriptions',
        'help_text': help_text,
        'base': 'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def process_project_report_photos(request, prh_id, pr_id):
    """ Processing the project report photos given by pr_id.

    If pr_id is zero then this starts at the beginning (a very fine place
    to start). This pulls all the photos for events associated with the
    project report (or the report itself) and has the user select which ones
    to ultimately include in the report.
    """
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    pr_header = get_object_or_404(ProjectReportHeader, id=prh_id)
    reports = pr_header.get_project_reports().order_by(
                                            'target_audience',
                                            'planning_start_date',
                                            'id',
    )

    if int(pr_id) == 0:
        # get started
        pr = reports[0]
        next_index = 1
    else:
        # process the current report
        pr = get_object_or_404(ProjectReport, id=pr_id)
        for index, item in enumerate(reports):
            if item == pr:
                next_index = index+1
                break
    photo_query = EventPhoto.objects.filter(
                    (Q(event__project_report=pr) & Q(project_report=None)) |
                    Q(project_report=pr)
    )
    needs_redirect = False
    # some reports will not have photos. If they do not, skip to the next
    # one that does
    while not photo_query.exists():
        needs_redirect = True
        if next_index < reports.count():
            pr = reports[next_index]
            next_index += 1
            photo_query = EventPhoto.objects.filter(
                    (Q(event__project_report=pr) & Q(project_report=None)) |
                    Q(project_report=pr)
            )
        else:
            # if there are no more reports, move on to the next thing
            pr_header.finished_photos = True
            pr_header.save()
            return redirect('history:process_project_report_compilation')

    if needs_redirect:
        # jump to the next report which has photos
        pr_header.last_photo = pr.id
        pr_header.save()
        return redirect('history:process_project_report_photos',
                        pr_header.id,
                        pr.id)

    formset = ProjectPhotoFormset(
                    request.POST or None,
                    request.FILES or None,
                    queryset=photo_query
    )
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            request.session['success_message'] = 'Photos updated'
            if next_index < reports.count():
                pr_header.last_photo = reports[next_index].id
                pr_header.save()
                return redirect('history:process_project_report_photos',
                                pr_header.id,
                                reports[next_index].id)
            else:
                pr_header.finished_photos = True
                pr_header.save()
                return redirect('history:process_project_report_compilation')
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    template = loader.get_template('generic_formset.html')
    help_text = ('This is step 3 of 4. Please make updates to the project '
                 'descriptions as necessary. A suggested description based on '
                 'project leader submissions is pre-loaded below '
                 'for:\nProject Name: %s\nTerm: %s\nCategory: %s\nPlanning '
                 'Start: %s\nProject %d out of %d') % (
                                    pr.name,
                                    unicode(pr.term),
                                    pr.get_target_audience_display(),
                                    pr.planning_start_date,
                                    next_index,
                                    reports.count()
                )
    context_dict = {
        'formset': formset,
        'subnav': 'project_reports',
        'has_files': True,
        'submit_name': 'Confirm Photos: ' + pr.name,
        'can_add': True,
        'form_title': 'Create Project Reports: Project Photos',
        'help_text': help_text,
        'base': 'history/base_history.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def compile_project_reports(request, prh_id):
    """ Runs the actual compilation of the project reports. Generates a pdf.
    """
    if not Permissions.can_process_project_reports(request.user):
        raise PermissionDenied()
    prh = get_object_or_404(ProjectReportHeader, id=prh_id)
    errors = prh.write_tex_files()
    if errors:
        error_message = 'The following reports had the following error codes:'
        for error in errors:
            error_message = (error_message + '\n' +
                             error['report'] + ': %d' % (error['error_code']))
        request.session['error_message'] = unicode(errors)
    return redirect('history:process_project_report_compilation')
