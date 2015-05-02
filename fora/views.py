from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory,modelform_factory
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.template import RequestContext, loader
from django.utils import timezone

from django_ajax.decorators import ajax

from fora.models import Forum,ForumThread,ForumMessage,MessagePoint,get_user_points
from member_resources.views import get_permissions as get_member_permissions
from mig_main.utility import get_previous_page, get_message_dict, Permissions
from mig_main.models import MemberProfile
from mig_main.location_field import GeoLocation

# Create your views here.


def get_permissions(user):
    permission_dict=get_member_permissions(user)
    is_member=False
    if hasattr(user,'userprofile') and user.userprofile.is_member():
        is_member=True
    permission_dict.update({'can_create_thread':Permissions.can_create_thread(user),
                            'can_create_forum':Permissions.can_create_forum(user),
                            'can_comment':is_member,
                            'can_moderate':Permissions.can_create_forum(user),
                            'can_downvote':get_user_points(user.userprofile.memberprofile)>0 if is_member else False})
    
    return permission_dict
def get_common_context(request):
    links=[
        {
            'name': 'Submit Affirmation',
            'link': reverse('member_resources:submit_praise')
        },
    ]
    if hasattr(request.user,'userprofile') and request.user.userprofile.is_member():
        links.append({
                'name': 'View Member Map',
                'link': reverse('fora:view_map')
            }
        )
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
        threads=ForumThread.objects.filter(hidden=False).order_by('-time_created')
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
    if forum.forumthread_set.filter(hidden=False).exists():
        request.session['error_message']='Forum has visible threads, unable to delete'
        return get_previous_page(request,alternate='fora:index')
    forum.delete()
    return redirect('fora:index')

@ajax    
def upvote_comment(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    
    if profile in message.get_upvoters():
        request.session['error_message']='You have already upvoted this post'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    existing_downvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=False)
    existing_downvotes.delete()
    upvote=MessagePoint(user=profile,message=message,plus_point=True)
    upvote.save()
    return {'fragments':{'#upvote'+comment_id:r'''<a id="upvote%s" class="btn btn-warning" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Withdraw upvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:withdraw_upvote',args=[comment_id]),comment_id,comment_id),
        '#downvote'+comment_id:r'''<a id="downvote%s" class="btn btn-primary" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Switch to downvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:downvote_comment',args=[comment_id]),comment_id,comment_id),
        '#points'+comment_id:r'''<span id="points11">%d</span>'''%(message.get_net_points()),
    }}

@ajax    
def withdraw_upvote(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    existing_upvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=True)
    existing_upvotes.delete()

    return {'fragments':{'#upvote'+comment_id:r'''<a id="upvote%s" class="btn btn-success" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Upvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:upvote_comment',args=[comment_id]),comment_id,comment_id),
        '#downvote'+comment_id:r'''<a id="downvote%s" class="btn btn-danger" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Downvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:downvote_comment',args=[comment_id]),comment_id,comment_id),
        '#points'+comment_id:r'''<span id="points11">%d</span>'''%(message.get_net_points()),
    }}

@ajax    
def withdraw_downvote(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    existing_downvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=False)
    existing_downvotes.delete()

    return {'fragments':{'#downvote'+comment_id:r'''<a id="downvote%s" class="btn btn-danger" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Downvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:downvote_comment',args=[comment_id]),comment_id,comment_id),
        '#upvote'+comment_id:r'''<a id="upvote%s" class="btn btn-success" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Upvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:upvote_comment',args=[comment_id]),comment_id,comment_id),
        '#points'+comment_id:r'''<span id="points11">%d</span>'''%(message.get_net_points()),
    }}
@ajax   
def downvote_comment(request,comment_id):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to vote'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    message=get_object_or_404(ForumMessage,id=comment_id)
    profile = request.user.userprofile.memberprofile
    if get_user_points(profile)<=0:
        request.session['error_message']='Downvoting costs 1 point. You lack sufficient points.'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    if profile in message.get_downvoters():
        request.session['error_message']='You have already downvoted this post'
        return {'fragments':{'#ajax-message':r'''<div id="ajax-message" class="alert alert-danger">
    <button type="button" class="close" data-dismiss="alert">&times</button>
    <strong>Error:</strong> %s</div>'''%(request.session.pop('error_message'))}}
    existing_upvotes = MessagePoint.objects.filter(user=profile,message=message,plus_point=True)
    existing_upvotes.delete()
    downvote=MessagePoint(user=profile,message=message,plus_point=False)
    downvote.save()
    return {'fragments':{'#downvote'+comment_id:r'''<a id="downvote%s" class="btn btn-primary" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Withdraw downvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:withdraw_downvote',args=[comment_id]),comment_id,comment_id),
        '#upvote'+comment_id:r'''<a id="upvote%s" class="btn btn-success" onclick="$('#downvote%s').attr('disabled',true);$('#upvote%s').attr('disabled',true);ajaxGet('%s',function(){$('#upvote%s').attr('disabled',false);$('#downvote%s').attr('disabled',false);})">Switch to Upvote</a>'''%(comment_id,comment_id,comment_id,reverse('fora:upvote_comment',args=[comment_id]),comment_id,comment_id),
        '#points'+comment_id:r'''<span id="points11">%d</span>'''%(message.get_net_points()),
    }}
    
@ajax
def get_thread_page(request,forum_id,page_num):
    page_num=int(page_num)
    forum = get_object_or_404(Forum,id=forum_id)
    threads = forum.get_thread_page(page_num)
    max_pages = forum.get_num_thread_pages()
    if page_num >0:
        down_options = r'''onclick="ajaxGet('%s',function(){})"'''%(reverse('fora:get_thread_page',args=[forum_id,page_num-1]))
    else:
        down_options = r'''class="disabled"'''
    if page_num < (max_pages-1):
        up_options = r'''onclick="ajaxGet('%s',function(){})"'''%(reverse('fora:get_thread_page',args=[forum_id,page_num+1]))
    else:
        up_options = r'''class="disabled"'''
    context_dict = {
        'forum':forum,
        'forum_threads':threads,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    thread_list_html = loader.render_to_string('fora/thread_list.html',context_dict)
    print thread_list_html
    return {'fragments':{'#forum_pager'+forum_id:r'''<ul class="pagination" id="forum_pager%s">
  <li><a href="#" %s>&laquo;</a></li>
  <li><a href="#" %s>&raquo;</a></li>
</ul>'''%(forum_id,down_options,up_options),
        '#forum_threads'+forum_id:thread_list_html}}
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
    
def view_map(request):
    if not hasattr(request.user,'userprofile') or not request.user.userprofile.is_member():
        request.session['error_message']='You must be logged in and a member to view this.'
        return get_previous_page(request,alternate='member_resources:index')
    members_with_location = MemberProfile.get_members().exclude(location='')
    template = loader.get_template('fora/map.html')
    member = request.user.userprofile.memberprofile
    context_dict = {
        'members':members_with_location,
        'center': member.location if member.location else GeoLocation(42.26,-83.7483),
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))