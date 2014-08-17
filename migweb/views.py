# Create your views here.
from datetime import date

from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.utils import timezone

from event_cal.models import CalendarEvent
from history.models   import WebsiteArticle
from mig_main.models import SlideShowPhoto
from mig_main.utility import get_quick_links, get_message_dict
from migweb.settings import DEBUG,DEBUG_user
def get_permissions(user):
    permission_dict={}
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({'request':request})
    return context_dict

def home(request):
    request.session['current_page']=request.path
    slideshow_photos = SlideShowPhoto.objects.filter(active=True)
    now = timezone.localtime(timezone.now())
    today=date.today()
    upcoming_events = CalendarEvent.get_upcoming_events()
    web_articles    = WebsiteArticle.objects.order_by('-date_posted').exclude(date_posted__gt=today)[:3]
    template = loader.get_template('home.html')
    context_dict = {
        'upcoming_events':upcoming_events,
        'web_articles':web_articles,
        'current_time':now,
        'request':request,
        'quick_links':get_quick_links(request.user),
        'slideshow_photos':slideshow_photos,
        'current_meetings':CalendarEvent.objects.filter(CalendarEvent.get_current_meeting_query()),
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def login_view(request):
    if DEBUG:
        user_name = DEBUG_user
    else:
        user_name = request.META['REMOTE_USER']
    users_w_name = User.objects.filter(username=user_name)
    if not users_w_name.exists():
        user = User.objects.create_user(user_name,user_name+'@umich.edu','')
    else:
        user = users_w_name[0]
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    user.save()
    login(request,user)
    if request.method=='POST':
        body = request.POST
    else:
        body = request.GET
    if 'next' in body:
        return redirect(body['next'])
    return redirect('home')
def logout_view(request):
    logout(request)
    if DEBUG:
        return redirect('/')
    else:
        return HttpResponseRedirect('https://weblogin.umich.edu/cgi-bin/logout?https://tbp.engin.umich.edu/')
