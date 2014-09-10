# Create your views here.
import json
from os.path import isfile

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,Http404
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.utils import timezone
import tweepy

from event_cal.models import CalendarEvent
from history.models   import WebsiteArticle
from mig_main.models import SlideShowPhoto
from mig_main.utility import get_quick_links, get_message_dict
from migweb.settings import DEBUG,DEBUG_user, twitter_token,twitter_secret
from migweb.profile_views import profile
def get_permissions(user):
    permission_dict={}
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({'request':request})
    return context_dict
@profile('home.prof')
def home(request):
    request.session['current_page']=request.path
    slideshow_photos = SlideShowPhoto.objects.filter(active=True)
    now = timezone.localtime(timezone.now())
    upcoming_events = CalendarEvent.get_upcoming_events()
    web_articles    = WebsiteArticle.get_stories()[:3]
    
    upcoming_html=loader.get_template('event_cal/upcoming_events.html').render(RequestContext(request,{'upcoming_events':upcoming_events,}))
    
    template = loader.get_template('home.html')
    context_dict = {
        'upcoming_events':upcoming_html,
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
    if 'next' in body and not body['next']=='':
        return redirect(body['next'])
    return redirect('home')
def logout_view(request):
    logout(request)
    if DEBUG:
        return redirect('/')
    else:
        return HttpResponseRedirect('https://weblogin.umich.edu/cgi-bin/logout?https://tbp.engin.umich.edu/')

def initialize_twitter(request):
    if not request.user.is_superuser:
        raise PermissionDenied()
    if isfile('/srv/www/twitter.dat'):
        request.session['error_message']='Twitter already initialized'
        return redirect('/')
    auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError as e:
        print e
        request.session['error_message']= 'Error! Failed to get request token.'
        return redirect('/')
    request.session['request_token']=(auth.request_token.key,auth.request_token.secret)
    return redirect(redirect_url)
def twitter_oauth(request):
    if not request.user.is_superuser:
        raise PermissionDenied()
    verifier = request.GET['oauth_verifier']
    auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
    token = request.session.pop('request_token',None)
    if not token:
        request.session['error_message']='Unable to load twitter token'
        return redirect('/')
    auth.set_request_token(token[0], token[1])

    try:
        auth.get_access_token(verifier)

    except tweepy.TweepError:
        request.session['error_message']='Unable to get access token'
        return redirect('/')
    f = open('/srv/www/twitter.dat','w')
    json.dump((auth.access_token.key,auth.access_token.secret),f)
    f.close()
    request.session['success_message']='Website successfully authorized'
    return redirect('/')
