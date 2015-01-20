#The views associated with the Elections widget
import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelform_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext, loader
from django.utils.encoding import force_unicode

from markdown import markdown

from elections.models import Election, Nomination
from elections.forms import NominationForm
from member_resources.views import get_permissions as get_member_permissions
from mig_main.models import UserProfile, OfficerPosition, AcademicTerm, MemberProfile, OfficerTeam
from mig_main.utility import get_message_dict,Permissions


def get_permissions(user):
    permission_dict = get_member_permissions(user)
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'main_nav':'members',
        'elections':Election.get_current_elections(),
        'subnav':'elections',
        })
    return context_dict

def index(request):
    request.session['current_page']=request.path
    template = loader.get_template('elections/index.html')
    current_elections=Election.get_current_elections()
    context_dict = {
        'current_elections':current_elections,
    }
    if current_elections.count()==1:
        return redirect('elections:list',current_elections[0].id)
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def list(request,election_id):
    request.session['current_page']=request.path
    e=get_object_or_404(Election,id=election_id)
    nominees = e.nomination_set.exclude(accepted=False)
    context_dict = {
            'nominees':nominees,
            'election':e,
            'subsubnav':'list'+election_id,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('elections/list.html')
    return HttpResponse(template.render(context))

def positions(request,election_id):
    request.session['current_page']=request.path
    positions=OfficerPosition.get_current()
    context_dict = {
            'subsubnav':'positions'+election_id,
            'positions':positions,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('elections/positions.html')
    return HttpResponse(template.render(context))

def my_nominations(request,election_id):
    if not Permissions.can_nominate(request.user):
        request.session['error_message']='You must be logged in, have a profile, and be a member to view nominations.'
        return redirect('elections:index')
    e=get_object_or_404(Election,id=election_id)
    noms = Nomination.objects.filter(nominee=request.user.userprofile.memberprofile,election=e)
    context_dict = {
            'my_nominations':noms,
            'election':e,
            'subsubnav':'my_nominations'+election_id,
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('elections/my_nominations.html')
    return HttpResponse(template.render(context))


@login_required
def nominate(request,election_id):
    base_web = r'https://tbp.engin.umich.edu/'
    if not Permissions.can_nominate(request.user):
        request.session['error_message']='You must be logged in, have a profile, and be a member to submit a nomination'
        return redirect('elections:index')
    request.session['current_page']=request.path
    e=get_object_or_404(Election,id=election_id)
    nomination = Nomination(election=e)
    nomination.nominator = request.user.userprofile
    if request.method =='POST':
        form = NominationForm(request.POST,instance=nomination,election=e)
        if form.is_valid():
            existing_nominations = Nomination.objects.filter(nominee=form.cleaned_data['nominee'],position=form.cleaned_data['position'],election=e)
            instance = form.save(commit=False)
            if existing_nominations.exists():
                if instance.nominee == request.user.userprofile.memberprofile:
                    existing_nominations[0].accepted=True
                    existing_nominations[0].save()
                    request.session['success_message']='Your self nomination was successfully submitted and accepted.'
                else:
                    request.session['warning_message']='This nomination has been previously submitted.'
            elif instance.nominee == request.user.userprofile.memberprofile:
                instance.accepted=True
                instance.save()
                request.session['success_message']='Your self nomination was successfully submitted and accepted.'
            else:
                instance.save()
                #TODO move these to a more sensible location and use kyle & my email script
                recipient = instance.nominee
                instance.position
                recipient_email = recipient.get_email()
                position=instance.position
                url_stem = base_web+reverse('elections:accept_or_decline_nomination',args=(instance.id,))
                accept_link = url_stem+r'?accept=YES'
                decline_link = url_stem+r'?accept=NO'
                if position.team_lead.exists():
                    team_lead_bit = '**Team Lead:** '+' and '.join( unicode(x) for x in position.team_lead.all())
                else:
                    team_lead_bit = ''
                if position.team_lead.count() < position.members.count():
                    if position.members.count() > 1:
                        team_member_bit = '**Teams:** '
                    else:
                        team_member_bit = ''
                    team_member_bit+= ' and '.join(unicode(x) for x in position.members.all())
                else:
                    team_member_bit=''
                body = r'''Hello %(name)s,
            
You've been nominated for %(position)s!
Here's some information on it:

%(team_info)s

%(description)s
            
To accept the nomination please click this link: %(accept_link)s
or to decline click this link: %(decline_link)s
            
You can also accept or decline by visiting the website.
            
Regards,
The TBP Election Chairs
tbp-elections@umich.edu'''%{'name':recipient.get_casual_name(),'position':position.name,
        'description':position.description,'accept_link':accept_link,'decline_link':decline_link,'team_info':team_lead_bit+'\n'+team_member_bit}
                html_body=markdown(force_unicode(body),['nl2br'],safe_mode=True,enable_attributes=False)
                msg = EmailMultiAlternatives('You\'ve been nominated for an officer position!',body,'tbp-elections@umich.edu',[recipient_email])
                msg.attach_alternative(html_body,"text/html")
                msg.send()
                #send_mail('You\'ve been nominated for an officer position!',body,'tbp-elections@umich.edu',[recipient_email],fail_silently=False)
                request.session['success_message']='Your nomination was successfully submitted, and the nominee emailed.'
            return HttpResponseRedirect(reverse('elections:list', args=(election_id,)))
        else:
            request.session['error_message']='There were errors in your submission'
    else:
        form = NominationForm(instance=nomination,election=e)
    context_dict = {
        'form':form,
        'has_files':False,
        'submit_name':'Submit Nomination',
        'back_button':{'link':reverse('elections:list',args=(election_id,)),'text':'List of Nominees'},
        'form_title':'Election Nomination',
        'help_text':'Choose a member to nominate for an officer position. If you nominate someone other than yourself, they will be emailed to determine their acceptance.',
        'base':'elections/base_elections.html',
        'subsubnav':'list',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_form.html')
    return HttpResponse(template.render(context))

def accept_or_decline_nomination(request,nomination_id):
    if not Permissions.can_nominate(request.user):
        request.session['error_message']='You must be logged in, have a profile, and be a member to accept/decline a nomination.'
        return redirect('elections:index')
    nom = get_object_or_404(Nomination,id=nomination_id)
    if not nom.nominee == request.user.userprofile.memberprofile:
        request.session['error_message']='You can only accept or decline your own nominations.'
        return redirect('elections:index')
        

    if request.method=='POST':
        request_body = request.POST
    else:
        request_body = request.GET

    if request_body.__contains__('accept'):
        accepted= (request_body.__getitem__('accept')=='YES')
    nom.accepted=accepted
    nom.save()
    return HttpResponseRedirect(reverse('elections:my_nominations', args=(nom.election.id,)))
        
