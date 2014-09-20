"""
Contains all of the view logic associated with the about section of the webpage.
"""
from datetime import date
# Create your views here.

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse#, Http404, HttpResponseRedirect
from django.shortcuts import  get_object_or_404,redirect
from django.forms.models import modelformset_factory
from django.template import RequestContext, loader
from django.db.models import Q,Count

from django_ajax.decorators import ajax

from about.models import AboutSlideShowPhoto,JoiningTextField
from history.models import Officer
from mig_main.models import OfficerPosition, OfficerTeam, AcademicTerm
from mig_main.utility import get_message_dict,Permissions
from history.models import GoverningDocument, GoverningDocumentType,pack_officers_for_term
#from requirements.models import SemesterType


def get_permissions(user):
    """
    Standardized way of querying user permissions across the website. Permissions for the entire (or most of it) module are loaded into a dictionary that gets merged with the template context to provide the template with a list of permissions so as to generate the page correctly.
    """
    permission_dict={
            'can_edit_about_photos':Permissions.can_manage_website(user),
            }
    return permission_dict
def get_common_context(request):
    """
    Standardized way of providing context that will be needed by every or nearly every page within a module/section. Adds the request and other necessary context to a dictionary that later gets merged with the template context.
    """
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'main_nav':'about',
        })
    return context_dict



def index(request):
    """
    The landing page for the about section. Has some overview text (static) and a photo slideshow determined by the records in the AboutSlideShowPhoto table.
    """
    slideshow_photos = AboutSlideShowPhoto.objects.filter(active=True)
    template = loader.get_template('about/about.html')
    context_dict = {
        'slideshow_photos':slideshow_photos,
        'subnav':'about',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def eligibility(request):
    """
    The joining page. The name eligibility is a backwards compatibility to the old name of the page. Unfortunately changing the view names is a big hassle as all the links throughout the website are kind of based on those. Shows text determined by the JoiningTextField table and a static photo that desperately needs updating.
    """
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
            'subnav':'joining',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def update_about_photos(request):
    """
    Standard form view based on the generic_formset. Used to update the photos in the about landing page.
    """
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
        'subnav':'about',
        'has_files':True,
        'submit_name':'Update About Page Photos',
        'back_button':{'link':reverse('about:index'),'text':'To About Page'},
        'form_title':'Edit About Page Photos',
        'help_text':'These are the photos shown in the about page photo slideshow. You can omit a photo from being displayed by unchecking the \"Active\" option.',
        'can_add_row':True,
        'base':'about/base_about.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context))

def update_joining_page(request):
    """
    Standard form view based on the generic_formset. Used to update the text in the joining page.
    """
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
        'subnav':'joining',
        'has_files':False,
        'submit_name':'Update Joining Page',
        'back_button':{'link':reverse('about:eligibility'),'text':'To Joining Page'},
        'form_title':'Edit Joining Page Text',
        'help_text':'These sections use markdown syntax. You can change the content and how it is displayed here.',
        'can_add_row':False,
        'base':'about/base_about.html',
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    template = loader.get_template('generic_formset.html')
    return HttpResponse(template.render(context))
def leadership(request):
    """
    Shows the leadership page for the current term. Convenience function so that /leadership/ goes somewhere meaningful.
    """
    return leadership_for_term(request,AcademicTerm.get_current_term().id)

def leadership_for_term(request,term_id):
    """
    Shows the officers for the specified term. The packing logic that assembles officers into teams for dispaly is contained in the pack_officers_for_term function.

    """
    term = get_object_or_404(AcademicTerm,id=term_id)
    officers = pack_officers_for_term(AcademicTerm.objects.get(id=term_id))
    officer_set = Officer.objects.filter(term=term).values('id')
    template = loader.get_template('about/leadership.html')

    context_dict = {
        "officers":officers,
        'officer_ids':officer_set,
        'request':request,
        'terms':AcademicTerm.get_rchron_before()[:5],
        'requested_term':term,
        'is_current':(term_id==AcademicTerm.get_current_term().id),
        'subnav':'leadership',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
@ajax 
def officer(request,officer_id):
    officer = get_object_or_404(Officer,id=officer_id)
    is_not_advisor=True
    if officer.position.name=='Advisor':
        is_not_advisor=False

    context_dict = {
        'officer':officer,
        'is_not_advisor':is_not_advisor,
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    officer_html = loader.render_to_string('about/officer.html',context_dict)
    output = {'fragments':{'#officer'+officer_id:officer_html}}
    print output
    return output
def bylaws(request):
    """
    Nothing fancy here. Just shows the bylaws (does filter to only show the active ones).

    """
    template = loader.get_template('about/bylaws.html')

    context_dict = {
        'documents':GoverningDocument.objects.filter(active=True),
        'subnav':'bylaws',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
