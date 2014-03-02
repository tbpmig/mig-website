#The views associated with the Elections widget
import datetime

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from elections.models import Election, Nomination,TempNomination
from mig_main.models import UserProfile, OfficerPosition, AcademicTerm, MemberProfile
from elections.forms import NominationForm,TempNominationForm

from django.core.mail import send_mail

def get_current_election(term_name):
    e = get_object_or_404(Election,term=AcademicTerm.objects.get(id=term_name))
    current_elections = Election.objects.filter(open_date__lte=datetime.date.today())
    current_elections = current_elections.filter(close_date__gte=datetime.date.today())
    if e not in current_elections:
        raise Http404
    return e

def index(request):
    request.session['current_page']=request.path
    current_elections = Election.objects.filter(open_date__lte=datetime.date.today())
    current_elections = current_elections.filter(close_date__gte=datetime.date.today())
    template = loader.get_template('elections/temp_index.html')
    context = RequestContext(request, {
        'current_elections':current_elections,
        'request':request,
    })
    if current_elections:
        return list(request,current_elections[0].term.id)
    
    return HttpResponse(template.render(context))
    
def list(request,term_name):
    request.session['current_page']=request.path
    e=get_current_election(term_name)       
    #nominees = e.nomination_set.exclude(accepted__exact=False)
    
    nominees = e.tempnomination_set.exclude(accepted__exact=False).order_by('id')
    return render(request, 'elections/temp_list.html', {'nominees':nominees,'term':term_name,'term_name':unicode(AcademicTerm.objects.get(id=term_name)),'request':request,})



def temp_nominate(request,term_name):
    base_web = r'http://tbp.engin.umich.edu:8000/'
    request.session['current_page']=request.path
    e=get_current_election(term_name)
    nomination = TempNomination(election=e)
#    nomination.nominator = request.user.userprofile
    if request.method =='POST':
        form = TempNominationForm(request.POST)
        if form.is_valid():
            existing_nominations = TempNomination.objects.filter(nominee=form.cleaned_data['nominee_uniqname']).filter(position=form.cleaned_data['position'])
            if existing_nominations:
                pass
            else:
                nomination.name = form.cleaned_data['nominee_name']
                nomination.nominee = form.cleaned_data['nominee_uniqname']
                nomination.position = form.cleaned_data['position']
                nomination.save()
                #TODO move these to a more sensible location and use kyle & my email script
                name = nomination.name
                recipient =nomination.nominee
                position =  nomination.position
                recipient_email = recipient+"@umich.edu"
                body = r'''Hello %(name)s,
            
You've been nominated for %(position)s!
Here's some information on it:
%(description)s
            
To accept (or decline) this nomination, please email tbp-elections@umich.edu            
            
Regards,
The TBP Election Chairs
tbp-elections@umich.edu'''%{'name':name,'position':position.name,
                                        'description':position.description}
                send_mail('You\'ve been nominated for an officer position!',body,'tbp-elections@umich.edu',[recipient_email],fail_silently=False)
            return HttpResponseRedirect(reverse('elections:list', args=(term_name,)))
    else:
        form = TempNominationForm()
    return render(request,'elections/temp_nominate.html',{'form':form,'term_name':term_name})

@login_required
def nominate(request,term_name):
    base_web = r'http://tbp.engin.umich.edu:8000/'
    request.session['current_page']=request.path
    e=get_current_election(term_name)
    nomination = Nomination(election=e)
    nomination.nominator = request.user.userprofile
    if request.method =='POST':
        form = NominationForm(request.POST,instance=nomination)
        if form.is_valid():
            form.save()
            #TODO move these to a more sensible location and use kyle & my email script
            recipient = MemberProfile.objects.get(uniqname=form['nominee'].value())
            position =  OfficerPosition.objects.get(id=form['position'].value())
            recipient_email = recipient.get_email()
            accept_link = base_web+r'members/elections/'+term_name+r'/acceptdecline/?user='+recipient.uniqname+r'&position='+str(position.id)+r'&accept=YES'
            decline_link = base_web+r'members/elections/'+term_name+r'/acceptdecline/?user='+recipient.uniqname+r'&position='+str(position.id)+r'&accept=NO'
            body = r'''Hello %(name)s,
            
You've been nominated for %(position)s!
Here's some information on it:
%(description)s
            
To accept the nomination please click this link: %(accept_link)s
or to decline click this link: %(decline_link)s
            
You can also accept or decline by visiting the website.
            
Regards,
The TBP Election Chairs
tbp-elections@umich.edu'''%{'name':recipient.get_casual_name(),'position':position.name,
                                        'description':position.description,'accept_link':accept_link,'decline_link':decline_link}
            send_mail('You\'ve been nominated for an officer position!',body,'tbp-elections@umich.edu',[recipient_email],fail_silently=False)
            return HttpResponseRedirect(reverse('elections:list', args=(term_name,)))
    else:
        form = NominationForm(instance=nomination)
    return render(request,'elections/nominate.html',{'form':form,'term_name':term_name})

def accept_or_decline_nomination(request,term_name):
    request.session['current_page']=request.path
    e=get_current_election(term_name)
    if request.method=='POST':
        request_body = request.POST
    else:
        request_body = request.GET
    if request_body.__contains__('user'):
        request.session['user'] = request_body.__getitem__('user')
    if request_body.__contains__('position'):
        request.session['position'] = request_body.__getitem__('position')
        print request.session['position']
    if request_body.__contains__('accept'):
        request.session['accept'] = request_body.__getitem__('accept')
    if not request.user.is_authenticated():
        return redirect('/accounts/login/?next=%s'%(request.path))
    if not request.user.userprofile.uniqname == request.session['user']:
        raise PermissionDenied
    nominations = Nomination.objects.filter(election=e,nominee__uniqname=request.session['user'],position__id=int(request.session['position']))
    first_pass = True
    for nom in nominations:
        if first_pass:
            first_pass = False
            nom.accepted=(request.session['accept']=='YES')
            nom.save()
        else:
            nom.delete()
    return HttpResponseRedirect(reverse('elections:list', args=(term_name,)))
        
