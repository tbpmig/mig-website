from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory,modelform_factory
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.template import RequestContext, loader
from django.utils import timezone

from fora.models import Forum,ForumThread,ForumMessage,MessagePoint
from member_resources.views import get_permissions as get_member_permissions
from mig_main.utility import get_previous_page, get_message_dict, Permissions

# Create your views here.


def get_permissions(user):
    permission_dict=get_member_permissions(user)
    permission_dict.update({'can_create_thread':Permissions.can_create_thread(user),
                            'can_create_forum':Permissions.can_create_forum(user),
                            'can_comment':hasattr(user,'userprofile') and user.userprofile.is_member(),
                            'can_moderate':Permissions.can_create_forum(user),})
    
    return permission_dict
def get_common_context(request):
    links=[]
    links.append({'name':'Submit Affirmation','link':reverse('member_resources:submit_praise')})
    context_dict=get_message_dict(request)
    context_dict.update({
        'subnav':'playground',
        'links':links,
        'profile':request.user.userprofile.memberprofile if (hasattr(request.user, 'userprofile') and request.user.userprofile.is_member()) else None,
        })
    return context_dict

def index(request):
    return view_thread(request,None)
    
def view_thread(request,thread_id):
    request.session['current_page']=request.path
    template = loader.get_template('fora/fora.html')
    fora = Forum.objects.all()
    if thread_id:
        active_thread=get_object_or_404(ForumThread,id=thread_id)
    else:
        threads=ForumThread.objects.filter(hidden=False).order_by('time_created')
        if threads.exists():
            active_thread=threads[0]
        else:
            active_thread=None
    reply_form = modelform_factory(ForumMessage,exclude=('forum_thread','in_reply_to','creator','time_created','last_modified','score','hidden'))
    context_dict = {
            'fora':fora,
            'active_thread':active_thread,
            'form':reply_form(),
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))   
def create_thread(request,forum_id):
    if not Permissions.can_create_thread(request.user):
        raise PermissionDenied()
    return add_comment(request,forum_id,None)

def create_forum(request):
    if not Permissions.can_create_forum(request.user):
        raise PermissionDenied()
    
    NewForumForm = modelform_factory(Forum)
    if request.method =='POST':
        form = NewForumForm(request.POST)
        if form.is_valid():
            form.save()
            request.session['success_message']='Forum successfully created'
            return get_previous_page(request,alternate='fora:index')
        else:
            request.session['warning_message']='There were errors in your submission'
    else:
        form = NewForumForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'has_files':False,
        'submit_name':'Create new forum',
        'form_title':'Create new forum',
        'help_text':'A new forum should be organized around a topic or a style of post.',
        'base':'fora/base_fora.html',
        'back_button':{'link':reverse('fora:index'),'text':'Back to fora'},
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))  

def hide_comment(request,comment_id):
    if not Permissions.can_create_forum(request.user):
        request.session['error_message']='You are not authorized to hide comments'
        return redirect('fora:index')
    message = get_object_or_404(ForumMessage,id=comment_id)
    message.hidden=True
    message.save()
    if not message.in_reply_to:
        thread =message.forum_thread
        thread.hidden=True
        thread.save()
        return redirect('fora:index')
    return get_previous_page(request,alternate='fora:index')
def delete_forum(request,forum_id):
    if not Permissions.can_create_forum(request.user):
        request.session['error_message']='You are not authorized to delete fora'
        return redirect('fora:index')
    forum=get_object_or_404(Forum,id=forum_id)
    forum.delete()
    return redirect('fora:index')
    
def upvote_comment(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return redirect('fora:index')
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    if profile in message.get_upvoters():
        request.session['error_message']='You have already upvoted this post'
        return get_previous_page(request,alternate='fora:index')
    existing_downvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=False)
    existing_downvotes.delete()
    upvote=MessagePoint(user=profile,message=message,plus_point=True)
    upvote.save()
    return get_previous_page(request,alternate='fora:index')
def withdraw_upvote(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return redirect('fora:index')
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    existing_upvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=True)
    existing_upvotes.delete()

    return get_previous_page(request,alternate='fora:index')
    
def withdraw_downvote(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return redirect('fora:index')
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    existing_downvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=False)
    existing_downvotes.delete()

    return get_previous_page(request,alternate='fora:index')
    
def downvote_comment(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return redirect('fora:index')
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    if profile in message.get_downvoters():
        request.session['error_message']='You have already downvoted this post'
        return get_previous_page(request,alternate='fora:index')
    existing_upvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=True)
    existing_upvotes.delete()
    downvote=MessagePoint(user=profile,message=message,plus_point=False)
    downvote.save()
    return get_previous_page(request,alternate='fora:index')
def add_comment(request,forum_id,reply_to_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        raise PermissionDenied()
    creator = request.user.userprofile.memberprofile
    forum=get_object_or_404(Forum,id=forum_id)
    if reply_to_id:
        op=get_object_or_404(ForumMessage,id=reply_to_id)

    AddCommentForm = modelform_factory(ForumMessage,exclude=('forum_thread','in_reply_to','creator','time_created','last_modified','score','hidden'))
    if request.method =='POST':
        form = AddCommentForm(request.POST)
        if form.is_valid():
            instance=form.save(commit=False)
            if reply_to_id:
                instance.in_reply_to=op
                instance.forum_thread=op.forum_thread
            else:
                ft = ForumThread(title=instance.title,forum=forum,creator=creator)
                ft.save()
                instance.in_reply_to=None
                instance.forum_thread=ft
            instance.creator=creator
            instance.save()
            request.session['success_message']='Comment successfully added' if reply_to_id else 'Thread successfully created'
            return get_previous_page(request,alternate='fora:index')
        else:
            request.session['warning_message']='There were errors in your submission'
    else:
        form = AddCommentForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'has_files':False,
        'submit_name':'Add Comment' if reply_to_id else 'Add new thread',
        'form_title':'Add Comment' if reply_to_id else 'Add new thread',
        'help_text':'Post a comment to the forum.' if reply_to_id else 'Create a new thread with the original post.',
        'base':'fora/base_fora.html',
        'back_button':{'link':reverse('fora:index'),'text':'Back to fora'},
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))