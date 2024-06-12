# Create your views here.
import json
from datetime import date, timedelta
from os.path import isfile

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.template import loader
from django.utils import timezone

from django_ajax.decorators import ajax
import tweepy

from event_cal.models import CalendarEvent, EventPhoto
from history.models import WebsiteArticle
from mig_main.models import SlideShowPhoto
from mig_main.utility import get_quick_links, get_message_dict
from migweb.settings import DEBUG, DEBUG_user, twitter_token, twitter_secret
from migweb.profile_views import profile


def get_permissions(user):
    """ Get permission bits that are required across all/most views.

    Currently just a placeholder.
    """
    permission_dict = {}
    return permission_dict


def get_common_context(request):
    """ Get the context bits that are common across many/all views.

    These often include things like the request object or model objects that
    are needed in several views.
    """
    context_dict = get_message_dict(request)
    context_dict.update({'request': request})
    return context_dict


def home(request):
    """ Returns a response object rendering the home page.

    Includes slideshow photos, upcoming events, and articles. It also contains
    information about meetings that are presently going on to ease the sign-in
    process.
    """
    request.session['current_page'] = request.path
    slideshow_photos = SlideShowPhoto.objects.filter(active=True)
    now = timezone.localtime(timezone.now())
    upcoming_events = CalendarEvent.get_upcoming_events()
    web_articles = WebsiteArticle.get_stories().exclude(date_posted__lt=date.today()-timedelta(days=60))
    upcoming_html = cache.get('upcoming_events_html', None)
    if not upcoming_html:
        upcoming_html = loader.render_to_string(
                            'event_cal/upcoming_events.html',
                            {'upcoming_events': upcoming_events, 'now': now}
                        )
        cache.set('upcoming_events_html', upcoming_html)
    template = loader.get_template('home.html')
    context_dict = {
        'upcoming_events': upcoming_html,
        'web_articles': web_articles,
        'current_time': now,
        'request': request,
        'quick_links': get_quick_links(request.user),
        'slideshow_photos': slideshow_photos,
        'current_meetings': CalendarEvent.objects.filter(
                                CalendarEvent.get_current_meeting_query()
                            ),
        'needs_social_media': True,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


@ajax
def get_slide_ajax(request, slide_id):
    """ Speeds up the homepage by returning slides via ajax as required/ready.

    Gets slides one at a time.
    """
    slide = get_object_or_404(SlideShowPhoto, id=slide_id)
    context_dict = {
        'slide': slide,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    slide_html = loader.render_to_string('slideshow_photo.html', context_dict)
    return {'fragments': {'#slideshow_photo'+slide_id: slide_html}}


@ajax
def get_eventphoto_ajax(request, photo_id):
    """ Speeds up form rendering by retrieving photos in lists via ajax.

    Gets photos one at a time. Used for events. Could be combined better
    with get_article_photo_ajax.
    """
    photo = get_object_or_404(EventPhoto, id=photo_id)
    context_dict = {
        'photo': photo,
        'for_event': True,
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    photo_html = loader.render_to_string('photo_dropdown.html', context_dict)
    return {'fragments': {'#eventphoto'+photo_id: photo_html}}


@ajax
def get_article_photo_ajax(request, photo_id):
    """ Speeds up form rendering by retrieving photos in lists via ajax.

    Gets photos one at a time. Used for articles. Could be combined better
    with get_eventphoto_ajax.
    """
    photo = get_object_or_404(EventPhoto, id=photo_id)
    context_dict = {
        'photo': photo,
        'for_event': False,
    }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    photo_html = loader.render_to_string('photo_dropdown.html', context_dict)
    return {'fragments': {'#eventphoto'+photo_id: photo_html}}


def cf_companies(request):
    """ Get the list of career fair companies, probably obsolete."""

    request.session['current_page'] = request.path
    template = loader.get_template('career_fair/CareerFairCompanySheet.html')
    context_dict = {}
    return HttpResponse(template.render(context_dict, request))


def login_view(request):
    """ Logs in the user. This page should be behind cosign and thus the login
    will already be completed.

    After logging in if they have a user object already it logs them in,
    otherwise it creates such an object and then logs them in.
    """
    if DEBUG:
        user_name = DEBUG_user
    else:
        uniqname,domain = request.META['REMOTE_USER'].split('@')
        if domain == 'umich.edu':
            user_name = uniqname
    users_w_name = User.objects.filter(username=user_name)
    if not users_w_name.exists():
        user = User.objects.create_user(user_name, user_name+'@umich.edu', '')
    else:
        user = users_w_name[0]
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    user.save()
    login(request, user)
    if request.method == 'POST':
        body = request.POST
    else:
        body = request.GET
    if 'next' in body and not body['next'] == '':
        return redirect(body['next'])
    return redirect('home')


def logout_view(request):
    """ Logs out the user and redirects them to the cosign logout page."""
    logout(request)
    if DEBUG:
        return redirect('/')
    else:
        return HttpResponseRedirect(
                ('https://weblogin.umich.edu/cgi-bin/logout'
                 '?https://tbp.engin.umich.edu/')
        )


def initialize_twitter(request):
    """ If the user is a superuser, sets up the site's twitter api.

    Used to begin the handshake with twitter oauth.
    """
    if not request.user.is_superuser:
        raise PermissionDenied()
    if isfile('/srv/www/twitter.dat'):
        request.session['error_message'] = 'Twitter already initialized'
        return redirect('/')
    auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError as e:
        print e
        request.session['error_message'] = 'Error! Failed to get token.'
        return redirect('/')
    request.session['request_token'] = (auth.request_token.key,
                                        auth.request_token.secret)
    return redirect(redirect_url)


def twitter_oauth(request):
    """ The second step in the twitter authentication chain."""
    if not request.user.is_superuser:
        raise PermissionDenied()
    verifier = request.GET['oauth_verifier']
    auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
    token = request.session.pop('request_token', None)
    if not token:
        request.session['error_message'] = 'Unable to load twitter token'
        return redirect('/')
    auth.set_request_token(token[0], token[1])

    try:
        auth.get_access_token(verifier)

    except tweepy.TweepError:
        request.session['error_message'] = 'Unable to get access token'
        return redirect('/')
    f = open('/srv/www/twitter.dat', 'w')
    json.dump((auth.access_token.key, auth.access_token.secret), f)
    f.close()
    request.session['success_message'] = 'Website successfully authorized'
    return redirect('/')
