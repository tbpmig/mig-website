from datetime import date
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
#from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext, loader
from history.models import WebsiteArticle, Publication
from mig_main.utility import Permissions, get_previous_page,get_message_dict
from history.forms  import ArticleForm, WebArticleForm

def get_permissions(user):
    permission_dict={
        'can_post':Permissions.can_post_web_article(user),
        'post_button':Permissions.can_upload_articles(user),
        }
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'main_nav':'publications',
        'new_bootstrap':True,
    })
    return context_dict

def get_article_view(request,article_id):
    request.session['current_page']=request.path
    today = date.today()
    web_articles    = WebsiteArticle.objects.order_by('-date_posted').exclude(date_posted__gt=today)
    if Permissions.can_post_web_article(request.user):
        if request.method == 'POST':
            form = WebArticleForm(request.POST)
            if form.is_valid():
                a=form.save()
                if hasattr(request.user,'userprofile') and request.user.userprofile.is_member():
                    a.created_by = request.user.userprofile.memberprofile
                    a.save()
                request.session['success_message']='Your webstory was posted successfully'
                return get_previous_page(request, 'history:index')
            else:
                request.session['error_message']='There were errors in your submission. Please correct the noted errors.'
        else:
            form = WebArticleForm(initial={'date_posted':today})
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
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def index(request):
    return get_article_view(request,None)
    

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
