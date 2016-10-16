import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelform_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext, loader

from elections.models import Election, Nomination
from elections.forms import NominationForm
from member_resources.views import get_permissions as get_member_permissions
from mig_main import messages
from mig_main.models import (
                AcademicTerm,
                MemberProfile,
                OfficerPosition,
                OfficerTeam,
                UserProfile,
)
from mig_main.utility import get_message_dict, Permissions


def get_permissions(user):
    permission_dict = get_member_permissions(user)
    return permission_dict


def get_common_context(request):
    context_dict = get_message_dict(request)
    context_dict.update({
        'request': request,
        'main_nav': 'members',
        'elections': Election.get_current_elections(),
        'subnav': 'elections',
        })
    return context_dict


def index(request):
    """ The landing page for the elections app.

    This page shows the currently active elections.
    If there is only one active election, it redirects to the nominations
    list instead.
    """
    request.session['current_page'] = request.path
    template = loader.get_template('elections/index.html')
    current_elections = Election.get_current_elections()
    context_dict = {}
    if current_elections.count() == 1:
        return redirect('elections:list', current_elections[0].id)
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    return HttpResponse(template.render(context_dict, request))


def list(request, election_id):
    """ The landing page for an individual election.

    It shows the list of currently accepted nominations, as well as
    options to nominate, or accept/decline nominations.
    """
    request.session['current_page'] = request.path
    e = get_object_or_404(Election, id=election_id)
    nominees = e.nomination_set.filter(accepted=True)
    context_dict = {
            'nominees': nominees,
            'election': e,
            'subsubnav': 'list'+election_id,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('elections/list.html')
    return HttpResponse(template.render(context_dict, request))


def positions(request, election_id):
    """ Shows a list of the officer positions and provides info about each."""
    request.session['current_page'] = request.path
    positions = OfficerPosition.get_current()
    context_dict = {
            'subsubnav': 'positions'+election_id,
            'positions': positions,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('elections/positions.html')
    return HttpResponse(template.render(context_dict, request))


def my_nominations(request, election_id):
    """ Lists an individual's nominations and provides the option to
    accept/decline.
    """
    if not Permissions.can_nominate(request.user):
        request.session['error_message'] = messages.ELECTION_NO_NOM_PERM
        return redirect('elections:index')
    e = get_object_or_404(Election, id=election_id)
    noms = Nomination.objects.filter(
                nominee=request.user.userprofile.memberprofile,
                election=e
    )
    context_dict = {
            'my_nominations': noms,
            'election': e,
            'subsubnav': 'my_nominations'+election_id,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('elections/my_nominations.html')
    return HttpResponse(template.render(context_dict, request))


@login_required
def nominate(request, election_id):
    """ Form view for submitting nominations.
    """
    if not Permissions.can_nominate(request.user):
        request.session['error_message'] = messages.ELECTION_NO_SUBMIT_NOM_PERM
        return redirect('elections:index')
    request.session['current_page'] = request.path
    e = get_object_or_404(Election, id=election_id)
    nomination = Nomination(election=e)
    nomination.nominator = request.user.userprofile
    form = NominationForm(
                request.POST or None,
                instance=nomination,
                election=e
    )
    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)
            nominee = instance.nominee
            position = instance.position
            existing_nominations = Nomination.objects.filter(
                                    nominee=nominee,
                                    position=position,
                                    election=e
            )
            if existing_nominations.exists():
                if instance.nominee == request.user.userprofile.memberprofile:
                    existing_nominations[0].accepted = True
                    existing_nominations[0].save()
                    msg = ('Your self nomination was successfully submitted '
                           'and accepted.')
                    request.session['success_message'] = msg
                else:
                    msg = 'This nomination has been previously submitted.'
                    request.session['warning_message'] = msg
            elif instance.nominee == request.user.userprofile.memberprofile:
                instance.accepted = True
                instance.save()
                msg = ('Your self nomination was successfully submitted '
                       'and accepted.')
                request.session['success_message'] = msg
            else:
                instance.save()
                instance.email_nominee()
                msg = ('Your nomination was successfully submitted, '
                       'and the nominee emailed.')
                request.session['success_message'] = msg
            return HttpResponseRedirect(
                        reverse('elections:list', args=(election_id,))
            )
        else:
            request.session['error_message'] = messages.GENERIC_SUBMIT_ERROR
    context_dict = {
        'form': form,
        'has_files': False,
        'submit_name': 'Submit Nomination',
        'back_button': {
                    'link': reverse(
                                'elections:list',
                                args=(election_id,)
                    ),
                    'text': 'List of Nominees'
        },
        'form_title': 'Election Nomination',
        'help_text': ('Choose a member to nominate for an officer position. '
                      'If you nominate someone other than yourself, they will '
                      'be emailed to determine their acceptance.'),
        'base': 'elections/base_elections.html',
        'subsubnav': 'list',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context_dict, request))


def accept_or_decline_nomination(request, nomination_id):
    """ 'View' that gets visited when an individual accepts/declines a
    nomination.
    """
    if not Permissions.can_nominate(request.user):
        request.session['error_message'] = messages.ELECTION_NO_ACCEPT_PERM
        return redirect('elections:index')
    nom = get_object_or_404(Nomination, id=nomination_id)
    if not nom.nominee == request.user.userprofile.memberprofile:
        request.session['error_message'] = ('You can only accept or decline '
                                            'your own nominations.')
        return redirect('elections:index')

    if request.method == 'POST':
        request_body = request.POST
    else:
        request_body = request.GET

    if request_body.__contains__('accept'):
        accepted = (request_body.__getitem__('accept') == 'YES')
    nom.accepted = accepted
    nom.save()
    return HttpResponseRedirect(
                    reverse('elections:my_nominations',
                            args=(nom.election.id,))
    )
