from datetime import date
# Create your views here.
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.shortcuts import  get_object_or_404,redirect
from django.forms.models import modelformset_factory
from django.template import RequestContext, loader
from django.db.models import Q

from about.models import AboutSlideShowPhoto,JoiningTextField
from history.models import Officer
from mig_main.models import OfficerPosition, OfficerTeam, AcademicTerm
from mig_main.default_values import get_current_term
from mig_main.utility import get_message_dict,Permissions
from history.models import GoverningDocument, GoverningDocumentType
#from requirements.models import SemesterType


def get_permissions(user):
    permission_dict={
            'can_edit_about_photos':Permissions.can_manage_website(user),
            }
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({'request':request})
    return context_dict
def get_terms():
    current = get_current_term()
    query = Q(year__lte=current.year)&~Q(semester_type__name='Summer')
    if current.semester_type.name=='Winter':
        query = query &~(Q(semester_type__name='Fall')&Q(year=current.year))
    terms = AcademicTerm.objects.filter(query)
    return terms.order_by('-year','semester_type__name')

def pack_officers_for_term(term):
    officer_set = Officer.objects.filter(term=term)
    term_advisors = officer_set.filter(position__name='Advisor')
    if term.year<2013 or (term.year==2013 and term.semester_type.name=='Winter'):
        term_officers = officer_set.filter(~Q(position__name='Advisor'))
    else:
        term_officers =[]
        for team in OfficerTeam.objects.all():
            disp_order = 1
            if team.name=='Executive Committee':
                disp_order = 0
            if team.name =='Electee and Membership Team':
                query = Q(position__in=team.members.all())&~Q(position__name='Vice President')
            else:
                query = Q(position__in=team.members.all())
            team_data={'order':disp_order,'name':team.name,'lead':team.lead.name,'officers':officer_set.filter(query)}
            term_officers.append(team_data)
    return {'officers':term_officers,'advisors':term_advisors}
def index(request):
    slideshow_photos = AboutSlideShowPhoto.objects.filter(active=True)
    template = loader.get_template('about/about.html')
    context_dict = {'slideshow_photos':slideshow_photos,}
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def eligibility(request):
    template = loader.get_template('about/eligibility.html')
    eligibility_text = JoiningTextField.objects.filter(section='EL')
    ugrad_reqs_text = JoiningTextField.objects.filter(section='UG')
    grad_reqs_text = JoiningTextField.objects.filter(section='GR')
    why_join_text = JoiningTextField.objects.filter(section='Y')
    context_dict = {
            'eligibility_text':eligibility_text,
            'ugrad_text':ugrad_reqs_text,
            'grad_text':grad_reqs_text,
            'why_join_text':why_join_text,
            'can_edit_page':Permissions.can_manage_electee_progress(request.user),
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def update_about_photos(request):
    if not Permissions.can_manage_website(request.user):
        request.session['error_message']='You are not authorized to update about page photos'
        return redirect('about:index')
    AboutPhotoForm = modelformset_factory(AboutSlideShowPhoto, can_delete=True)
    if request.method=='POST':
        formset = AboutPhotoForm(request.POST,request.FILES,prefix='about_photo')
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message']='About page photos successfully updated.'
            return redirect('about:index')
        else:
            request.session['error_message']='Your submision contained errors, please correct and resubmit.'
    else:
       formset=AboutPhotoForm(prefix='about_photo')
    context_dict = {
            'formset':formset,
            'prefix':'about_photo',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('about/update_about_photos.html')
    return HttpResponse(template.render(context))

def update_joining_page(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to update joining page text.'
        return redirect('about:eligibility')
    JoiningTextForm = modelformset_factory(JoiningTextField,extra=0)
    if request.method=='POST':
        formset = JoiningTextForm(request.POST)
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message']='Joining page successfully updated.'
            return redirect('about:eligibility')
        else:
            request.session['error_message']='Your submision contained errors, please correct and resubmit.'
    else:
       formset=JoiningTextForm()
    context_dict = {
            'formset':formset,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('about/joining_page_edit.html')
    return HttpResponse(template.render(context))
def leadership(request):
    return leadership_for_term(request,get_current_term().id)
def leadership_for_term(request,term_id):
    template = loader.get_template('about/leadership.html')
    term = get_object_or_404(AcademicTerm,id=term_id)
    if term.year<2013 or (term.year==2013 and term.semester_type.name=='Winter'):
        has_teams = False
    else:
        has_teams = True
    context_dict = {
        "officers":pack_officers_for_term(AcademicTerm.objects.get(id=term_id)),
        'request':request,
        'terms':get_terms()[:5],
        'requested_term':term,
        'is_current':(term_id==get_current_term().id),
        'has_teams':has_teams,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def bylaws(request):
    template = loader.get_template('about/bylaws.html')

    context_dict = {
        'documents':GoverningDocument.objects.filter(active=True),
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
