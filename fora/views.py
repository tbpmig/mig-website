from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.template import RequestContext, loader
from django.utils import timezone

from fora.models import Forum,ForumThread,ForumMessage,MessagePoint
from member_resources.views import get_permissions as get_member_permissions
from mig_main.utility import get_message_dict, Permissions

# Create your views here.


def get_permissions(user):
    permission_dict=get_member_permissions(user)
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    return context_dict

def index(request):
    request.session['current_page']=request.path
    template = loader.get_template('fora/fora.html')
    fora = Forum.objects.all()
    context_dict = {
            'fora':fora,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
