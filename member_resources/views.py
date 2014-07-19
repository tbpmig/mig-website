from datetime import date
import csv
from decimal import Decimal
import copy
import re
import logging

from django import forms
from django.http import HttpResponse, Http404 #HttpResponseRedirect
from django.shortcuts import  get_object_or_404
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.db import IntegrityError
from django.db.models import Max,Q
from django.core.exceptions import PermissionDenied
from django.forms.models import modelformset_factory, modelform_factory
from django.core.urlresolvers import reverse

from corporate.views import update_resume_zips
from electees.models import ElecteeGroup, electee_stopped_electing, EducationalBackgroundForm
from event_cal.models import CalendarEvent, MeetingSignInUserData,get_pending_events,get_events_w_o_reports
from history.models import Officer, MeetingMinutes,Distinction,NonEventProject,NonEventProjectParticipant
from member_resources.forms import MemberProfileForm, MemberProfileNewActiveForm, NonMemberProfileForm, MemberProfileNewElecteeForm, ElecteeProfileForm, ManageDuesFormSet, ManageUgradPaperWorkFormSet, ManageGradPaperWorkFormSet,ManageProjectLeadersFormSet, MassAddProjectLeadersForm, PreferenceForm,ManageInterviewsFormSet
from member_resources.forms import MeetingMinutesForm,ManageActiveGroupMeetingsFormSet,ManageElecteeStillElecting,LeadershipCreditFormSet,ManageActiveCurrentStatusFormSet,ManageElecteeDAPAFormSet,ElecteeToActiveFormSet
from member_resources.models import ActiveList, GradElecteeList, UndergradElecteeList, ProjectLeaderList
from migweb.context_processors import profile_setup
from mig_main.default_values import get_current_term
from mig_main.models import MemberProfile, Status, Standing, UserProfile, TBPChapter,AcademicTerm, CurrentTerm, SlideShowPhoto,UserPreference,TBPraise,PREFERENCES,get_members,get_actives,get_electees
from mig_main.utility import  Permissions, get_previous_page,get_next_term, get_next_full_term,get_current_event_leaders,get_current_officers,get_current_group_leaders,get_message_dict,UnicodeWriter
from outreach.models import TutoringRecord
from requirements.models import DistinctionType, Requirement, ProgressItem, EventCategory

INVALID_FORM_MESSAGE='The form is invalid. Please correct the noted errors.'

#LOGGING={
#    'version':1,
#    'disable_existing_loggers':False,
#    'handlers':{
#        'email':{
#            'level':'ERROR',
#            'class':'django.utils.log.AdminEmailHandler',
#            'include_html':True,
#        }
#    },
#    'loggers':{
#        'django.request':{
#            'handlers':['email'],
#            'level':'ERROR',
#            'propogate':True,
#        },
#    },
#}
#logging.config.dictConfig(LOGGING)
#logger = logging.getLogger('django.request')

def get_electees_with_status(distinction):
    
    query =  Q(distinction_type=distinction)& Q(term=get_current_term().semester_type)
    dist_standing = distinction.standing_type.all()
    requirements = Requirement.objects.filter(query)
    unflattened_reqs = package_requirements(requirements)
    electee_profiles = get_electees().filter(standing=dist_standing) 
    electees_with_status = []
    for profile in electee_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        amount_req = 0;
        amount_has = 0;
        has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
        if has_dist:
            electees_with_status.append(profile)
    return electees_with_status
def get_actives_with_status(distinction):
    query =  Q(distinction_type=distinction)& Q(term=get_current_term().semester_type)
    requirements = Requirement.objects.filter(query)
    unflattened_reqs = package_requirements(requirements)
    active_profiles = get_actives() 
    actives_with_status = []
    for profile in active_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        amount_req = 0;
        amount_has = 0;
        has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
        if has_dist:
            actives_with_status.append(profile)
    return actives_with_status
def get_electees_who_completed_reqs():
    ugrad_distinction =DistinctionType.objects.get(status_type__name="Electee",standing_type__name="Undergraduate",name='Electee (undergrad)') 
    grad_distinction =DistinctionType.objects.get(status_type__name="Electee",standing_type__name="Graduate",name='Electee (grad)') 
    ugrad_query = Q(distinction_type= ugrad_distinction)&Q(term=get_current_term().semester_type)
    grad_query = Q(distinction_type=grad_distinction)&Q(term=get_current_term().semester_type)
    
    ugrad_reqs = Requirement.objects.filter(ugrad_query)
    grad_reqs = Requirement.objects.filter(grad_query)
    unflattened_ugrad_reqs = package_requirements(ugrad_reqs)
    unflattened_grad_reqs = package_requirements(grad_reqs)
    ugrad_profiles = get_electees().filter(standing__name='Undergraduate').order_by('last_name')
    grad_profiles = get_electees().filter(standing__name='Graduate').order_by('last_name')
    electees_with_status = []
    for profile in ugrad_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        has_dist = has_distinction_met(packaged_progress,ugrad_distinction,unflattened_ugrad_reqs)
        if has_dist:
            electees_with_status.append(profile)
    for profile in grad_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        has_dist = has_distinction_met(packaged_progress,grad_distinction,unflattened_grad_reqs)
        if has_dist:
            electees_with_status.append(profile)
    return electees_with_status
def get_permissions(user):
    return {'extra_progress_tab':Permissions.can_view_more_than_own_progress(user),
    'misc_tab':(Permissions.can_manage_misc_reqs(user) or Permissions.can_change_requirements(user)),
    'can_manage_website':Permissions.can_manage_website(user),
    'can_access_history':Permissions.can_access_history(user),
    'can_access_playground':hasattr(user,'userprofile'),
    }
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'main_nav':'members',
        'new_bootstrap':True,
    })
    return context_dict

def saturate_hours(value):
    return min(value,15)
def add_child_reqs(sorted_reqs,requirements,parent):
    event_categories = EventCategory.objects.filter(parent_category=parent)
    for event_category in event_categories:
        reqs = requirements.filter(event_category=event_category)
        if reqs:
            sorted_reqs[event_category]={"children":add_child_reqs({},requirements,event_category),"requirements":reqs}
    return sorted_reqs

def get_events_signed_up_hours(uniqname):
    events_attending = CalendarEvent.objects.filter(eventshift__attendees__uniqname=uniqname).filter(completed=False).distinct()
    category_hours = {}
    for event in events_attending:
        if ProgressItem.objects.filter(member__uniqname=uniqname,related_event=event):
            continue
        if event.event_type not in category_hours:
            category_hours[event.event_type]=0
        shifts= event.eventshift_set.filter(attendees__uniqname=uniqname).order_by('start_time')
        n=shifts.count()
        count = 0
        hours=0
        while count< n:
            start_time = shifts[count].start_time
            end_time = shifts[count].end_time
            while count<(n-1) and shifts[count+1].start_time<end_time:
                count+=1
                end_time=shifts[count].end_time
            hours+=(end_time-start_time).seconds/3600.0
            count+=1
        if event.is_fixed_progress():
            category_hours[event.event_type]+=1
        else:
            category_hours[event.event_type]+=hours
    return category_hours
def package_requirements(requirements):
    sorted_reqs={}
    return add_child_reqs(sorted_reqs,requirements,None)
def package_progress(progress_items):
    packaged_progress={}
    for progress_item in progress_items:
        associated_event_type =progress_item.event_type
        if associated_event_type in packaged_progress.keys():
            packaged_progress[associated_event_type]['full']+=progress_item.amount_completed
            packaged_progress[associated_event_type]['sat']+=saturate_hours(progress_item.amount_completed)
        else:
            packaged_progress[associated_event_type]={'full':0,'sat':0}
            packaged_progress[associated_event_type]['full']=progress_item.amount_completed
            packaged_progress[associated_event_type]['sat']=saturate_hours(progress_item.amount_completed)
        while associated_event_type.parent_category!=None:
            associated_event_type = associated_event_type.parent_category
            if associated_event_type in packaged_progress.keys():
                packaged_progress[associated_event_type]['full']+=progress_item.amount_completed
                packaged_progress[associated_event_type]['sat']+=saturate_hours(progress_item.amount_completed)
            else:
                packaged_progress[associated_event_type]={'full':0,'sat':0}
                packaged_progress[associated_event_type]['full']=progress_item.amount_completed
                packaged_progress[associated_event_type]['sat']=saturate_hours(progress_item.amount_completed)
    return packaged_progress

def package_future_progress(packaged_progress,category_hours):
    ##TODO fix saturation
    future_progress = copy.deepcopy(packaged_progress)
    for event_type,hours in category_hours.items():
        if event_type in future_progress.keys():
            future_progress[event_type]['full']+=Decimal(hours)
            future_progress[event_type]['sat']+=Decimal(hours)
        else:
            future_progress[event_type]={'full':0,'sat':0}
            future_progress[event_type]['full']=Decimal(hours)
            future_progress[event_type]['sat']=Decimal(hours)
        event_type_temp = event_type
        while event_type_temp.parent_category!=None:
            event_type_temp = event_type_temp.parent_category
            if event_type_temp in future_progress.keys():
                future_progress[event_type_temp]['full']+=Decimal(hours)
                future_progress[event_type_temp]['sat']+=Decimal(hours)
            else:
                future_progress[event_type_temp]={'full':0,'sat':0}
                future_progress[event_type_temp]['full']=Decimal(hours)
                future_progress[event_type_temp]['sat']=Decimal(hours)
    return future_progress
                
def sorted_reqs2html_recursive(sorted_reqs,progress_items,distinctions,padding):
    html_string=''
    for event_category,data in sorted_reqs.items():
        html_string+='<tr><td style=\"padding-left:'+str(padding)+'em;\"><b>'+unicode(event_category)+'</b></td>\n'
        amount = 0
        if event_category in progress_items:
            if distinctions.count()>1 and progress_items[event_category]['sat']!=progress_items[event_category]['full']:
                amount = progress_items[event_category]['sat']
                html_string+="<td><p rel=\"tooltip\" data-trigger=\"hover\" data-toggle=\"popover\" data-placement=\"right\" data-content=\"Only 15 hours may be counted from a single event toward PA status. "+str(progress_items[event_category]['full'])+" total hours have been completed in this category.\">"+str(amount)+'*</p></td>\n'
            else:
                amount = progress_items[event_category]['full']
                html_string+="<td>"+str(amount)+'</td>\n'
        else:
            html_string+='<td>0</td>\n'
        for distinction in distinctions.order_by('name'):
            req = data["requirements"].filter(distinction_type=distinction)
            amount_req = 0
            if req:
                amount_req=req[0].amount_required
            html_string+='<td'
            if amount>=amount_req:
                html_string+=' class=\"requirement-met\"'
            html_string+='>'
            html_string+=str(amount_req)
            if amount>=amount_req:
                html_string+=' <i class=\"glyphicon glyphicon-ok\"></i>'
            html_string+='</td>\n'
        html_string+='</tr>\n'
        html_string+=sorted_reqs2html_recursive(data["children"],progress_items,distinctions,padding+2)
    return html_string

def has_distinction_met(progress,distinction,sorted_reqs):
    has_dist = True
    for event_category,data in sorted_reqs.items():
        if event_category in progress:
            if distinction.name=="Prestigious Active":
                amount = progress[event_category]['sat']
            else:
                amount = progress[event_category]['full']

        else:
            amount = 0
        req = data["requirements"].filter(distinction_type=distinction)
        amount_req = 0
        if req:
            amount_req = req[0].amount_required
        if amount_req>amount:
            return False
        has_dist = has_dist and has_distinction_met(progress,distinction,data["children"])
        if not has_dist:
            return False
    return has_dist

def flatten_reqs(sorted_reqs):
    flattened_reqs = []
    for event_category,data in sorted_reqs.items():
        flattened_reqs.append(event_category)
        if data["children"]:

            flattened_reqs.extend(flatten_reqs(data["children"]))
    return flattened_reqs
def flatten_progress(progress,reqs):
    flattened_progress = []
    for req in reqs:
        if req in progress:
            flattened_progress.append(progress[req])
        else:
            flattened_progress.append({'full':0,'sat':0})
    return flattened_progress

def sorted_reqs2html(sorted_reqs,progress_items,distinctions):
    html_string ='<table class="table table-striped table-bordered">\n<thead>\n<tr>\n<th>Requirement</th>\n'
    html_string+='<th>Completed</th>\n'
    if distinctions.count>1:
        html_string+='<th colspan ="%d">Requirement Statuses</th>\n'%(distinctions.count())
    else:
        html_string+='<th>Requirement for</th>\n'
    html_string+='</tr>\n<tr>\n<th></th>\n<th></th>'
    for distinction in distinctions.order_by('name'):
        html_string+='<th>'+distinction.name+'</th>\n'
    html_string+='</tr>\n</thead>'
    return html_string+sorted_reqs2html_recursive(sorted_reqs,progress_items,distinctions,0)+'</table>'

def user_is_member(user):
    if hasattr(user,'userprofile'):
        if user.userprofile.is_member():
            return True
    return False
## BEGIN VIEWS
def index(request):
    request.session['current_page']=request.path
    if user_is_member(request.user) and not 'error' in request.session:
        return redirect('member_resources:member_profiles')
    template = loader.get_template('member_resources/members.html')
    context_dict = {
        'subnav':'member_profiles',        
    }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
#this could be improved    
def member_profiles(request):
    request.session['current_page']=request.path
    if not user_is_member(request.user):
        request.session['error_message']='You must be logged in and a member to view member profiles.'
        return redirect('member_resources:index')
    template = loader.get_template('member_resources/userprofiles.html')
    context_dict = {
        'profiles':get_members(),
        'subnav':'member_profiles',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def profile(request,uniqname):
    request.session['current_page']=request.path
    if not user_is_member(request.user):
        request.session['error_message']='You must be logged in and a member to view member profiles.'
        return redirect('member_resources:index')
    template = loader.get_template('member_resources/userprofile.html')
    profile = get_object_or_404(MemberProfile,uniqname=uniqname)
    praise = TBPraise.objects.filter(recipient=profile)
    is_user = request.user.userprofile.uniqname==uniqname
    distinctions = DistinctionType.objects.filter(status_type=profile.status, standing_type=profile.standing).distinct()
    distinction_terms = []
    has_distinctions = False
    for distinction in distinctions:
        terms = Distinction.objects.filter(member=profile,distinction_type=distinction).count()
        if terms:
            has_distinctions = True
        distinction_terms.append({'name':distinction.name,'terms':terms})
    officer_positions=[]
    for position in Officer.objects.filter(user=profile):
        for term in position.term.all():
            officer_positions.append({'name':position.position.name,'term':term})

    context_dict = {
        'profile':profile,
        'officer_positions':sorted(officer_positions, key=lambda k: (-k['term'].year, k['term'].semester_type.name)),
        'awards':profile.award_set.all(),
        'distinction_terms':distinction_terms,
        'is_user':is_user,
        'edit':False,
        'has_distinctions':has_distinctions,
        'subnav':'member_profiles',
        'praise':praise,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def profile_edit(request,uniqname):
    request.session['current_page']=request.path
    if not user_is_member(request.user):
        request.session['error_message']='You must be logged in and a member to view member profiles.'
        return redirect('member_resources:index')
    is_user = False
    if hasattr(request.user,'userprofile'):
        is_user = request.user.userprofile.uniqname==uniqname
    if not (is_user or request.user.is_superuser):
        request.session['error_message']="You are not authorized to edit this profile"
        return redirect('member_resources:profile', uniqname)
    profile = MemberProfile.objects.get(uniqname__exact=uniqname)
    if request.method == 'POST':
        if profile.status.name == 'Active':
            form = MemberProfileForm(request.POST, request.FILES, instance= profile)
        else:
            form = ElecteeProfileForm(request.POST, request.FILES, instance= profile)
        if form.is_valid():
            form.save()
            #update_resume_zips()
            if is_user:
                intro_string = 'Your'
            else:
                intro_string = profile.get_firstlast_name()+'\'s'
            request.session['success_message']=intro_string+' profile was updated successfully.'
            return redirect('member_resources:profile', uniqname)
        else:
            request.session['error_message']='The form is invalid, please correct the errors noted below.'
    else:
        if profile.status.name == 'Active':
            form = MemberProfileForm(instance=MemberProfile.objects.get(uniqname__exact=uniqname))
        else:
            form = ElecteeProfileForm(instance=MemberProfile.objects.get(uniqname__exact=uniqname))
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'dp_ids':['id_expect_grad_date'],
        'subnav':'member_profiles',
        'has_files':True,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Profile',
        'back_button':{'link':reverse('member_resources:profile',args=[uniqname]),'text':'To %s\'s Profile'%(profile.get_firstlast_name())},
        'form_title':'Edit %s\'s Profile'%(unicode(profile)),
        'help_text':'Make updates to your profile here. Of special note, resumes must be submitted in pdf format.',
        'extra_js':['profile_edit_extras.html'],
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def profile_create(request):
    if not request.user.is_authenticated():
        request.session['error_message'] = 'You must be logged in to create a profile'
        if 'current_page' not in request.session:
            return redirect('home')
        else:
            return redirect(request.session['current_page'])
    request.session['current_page']=request.path
    user_info = profile_setup(request)
    if not user_info["needs_profile"]:
        request.session['warning_message'] ='You already have a profile. Please edit that instead.'
        return redirect('member_resources:profile', request.user.username)
    
    if user_info["is_active_member"]:
        
        if request.method =='POST':
            user_profile = MemberProfile(uniqname=request.user.username,user=request.user)
            user_profile.status = Status.objects.get(name='Active')
            form = MemberProfileNewActiveForm(request.POST,request.FILES,instance=user_profile)
            if form.is_valid():
                form.save()
                #update_resume_zips()
                request.session['success_message']='Profile created successfully.'
                return redirect('member_resources:profile',request.user.username)
            else:
                request.session['error_message']='The form is invalid, please correct the errors noted below.'
        else:
            form = MemberProfileNewActiveForm()
    elif user_info["is_grad_electee"] or user_info["is_ugrad_electee"]:
        if request.method =='POST':
            user_profile = MemberProfile(uniqname=request.user.username,user=request.user)
            user_profile.status = Status.objects.get(name='Electee')
            if user_info["is_grad_electee"]:
                user_profile.standing = Standing.objects.get(name='Graduate')
            else:
                user_profile.standing = Standing.objects.get(name='Undergraduate')
            user_profile.init_chapter = TBPChapter.objects.get(state='MI',letter='G')
            user_profile.init_term = get_current_term()
            form = MemberProfileNewElecteeForm(request.POST,request.FILES,instance=user_profile)
            if form.is_valid():
                form.save()
                request.session['success_message']='Profile created successfully.'
                return redirect('member_resources:profile',request.user.username)
            else:
                request.session['error_message']='The form is invalid, please correct the errors noted below.'
        else:
            form = MemberProfileNewElecteeForm()
    else:
        if request.method =='POST':
            user_profile = UserProfile(uniqname=request.user.username,user=request.user)
            form =NonMemberProfileForm(request.POST,instance=user_profile)
            if form.is_valid():
                form.save()
                request.session['success_message']='Profile created successfully.'
                return redirect('home')
            else:
                request.session['error_message']='The form is invalid, please correct the errors noted below.'
        else:
            form = NonMemberProfileForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'dp_ids':['id_expect_grad_date'],
        'subnav':'member_profiles',
        'has_files':True,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Create Profile',
        'form_title':'Create Your Profile',
        'help_text':'Make your profile here. Of special note, resumes must be submitted in pdf format.',
        'extra_js':['profile_edit_extras.html'],
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def edit_progress(request,uniqname):
    profile = get_object_or_404(MemberProfile,uniqname=uniqname)
    if profile.status.name=='Active':
        if not Permissions.can_manage_active_progress(request.user):
            request.session['error_message']='You are not authorized to edit this member\'s progress.'
            return redirect('member_resources:index')
    else:
        if not Permissions.can_manage_electee_progress(request.user):
            request.session['error_message']='You are not authorized to edit this member\'s progress.'
            return redirect('member_resources:index')
    term = get_current_term()
    progress_formset = modelformset_factory(ProgressItem,exclude=('member','term'),can_delete=True)
    if request.method =='POST':
        formset = progress_formset(request.POST,prefix='edit_progress',queryset=ProgressItem.objects.filter(term=term,member=profile))
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.member = profile
                instance.term = term
                instance.save()
            request.session['success_message']='Progress successfully updated.'
            return redirect('member_resources:view_progress',uniqname)
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = progress_formset(prefix='edit_progress',queryset=ProgressItem.objects.filter(term=term,member=profile))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'edit_progress',
        'subnav':'view_others_progress',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Submit Progress Items',
        'back_button':{'link':reverse('member_resources:view_progress',args=[uniqname]),'text':'To %s\'s Progress'%(profile.get_firstlast_name())},
        'form_title':'Edit Progress for %s'%(unicode(profile)),
        'help_text':'',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def view_progress(request,uniqname):
    if not Permissions.can_view_others_progress(request.user,uniqname):
        request.session['error_message']='You are not authorized to view this member\'s progress.'
        return redirect('member_resources:index')
    profile = get_object_or_404(MemberProfile,uniqname=uniqname)
#    if request.user.is_authenticated() and request.user.username == uniqname:
#        pass
#    else:
#        raise PermissionDenied()
#    if hasattr(request.user,'userprofile') and request.user.userprofile.is_member():
#        profile = request.user.userprofile.memberprofile
#    else:
#        raise Http404
    distinctions = DistinctionType.objects.filter(status_type=profile.status, standing_type=profile.standing).distinct()
    if profile.status.name=='Active':
        can_edit_progress=Permissions.can_manage_active_progress(request.user)
    else:
        can_edit_progress=Permissions.can_manage_electee_progress(request.user)
    query = Q()
    for distinction in distinctions:
        query = query | Q(distinction_type=distinction)
    query = query & Q(term=get_current_term().semester_type)
    requirements = Requirement.objects.filter(query)
    sorted_reqs = package_requirements(requirements)
    progress = ProgressItem.objects.filter(member=profile,term=get_current_term())
    is_own_progress = False
    if request.user.username == uniqname:
        is_own_progress = True
    events_attending = CalendarEvent.objects.filter(eventshift__attendees__uniqname=uniqname).filter(completed=False).distinct()
    events_signed_up_for = []
    category_hours = {}
    for event in events_attending:
        if ProgressItem.objects.filter(member__uniqname=uniqname,related_event=event):
            continue
        if event.event_type not in category_hours:
            category_hours[event.event_type]=0
        shifts= event.eventshift_set.filter(attendees__uniqname=uniqname).order_by('start_time')
        event_summary = {'category':event.event_type,'name':event.name,'end_date':None,'hours':0}
        n=shifts.count()
        count = 0
        hours=0
        while count< n:
            start_time = shifts[count].start_time
            end_time = shifts[count].end_time
            while count<(n-1) and shifts[count+1].start_time<end_time:
                count+=1
                end_time=shifts[count].end_time
            hours+=(end_time-start_time).seconds/3600.0
            count+=1
        if event.is_fixed_progress():
            category_hours[event.event_type]+=1
            event_summary['hours']+=1
        else:
            category_hours[event.event_type]+=hours
            event_summary['hours']+=hours
        if n:
            event_summary['end_date']=end_time
        events_signed_up_for.append(event_summary)
    template = loader.get_template('member_resources/view_progress.html')
    packaged_current_progress=package_progress(progress)
    packaged_future_progress=package_future_progress(packaged_current_progress,category_hours)
    if is_own_progress:
        subnav='view_own_progress'
    else:
        subnav='view_others_progress'
    context_dict = {
        'profile':profile,
        'reqs_html':sorted_reqs2html(sorted_reqs,package_progress(progress),distinctions),
        'reqs_html_future':sorted_reqs2html(sorted_reqs,packaged_future_progress,distinctions),
        'is_own_progress':is_own_progress,
        'progress_items':progress,
        'events_signed_up_for':events_signed_up_for,
        'category_hours':category_hours,
        'can_edit_progress':can_edit_progress,
        'subnav':subnav,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def view_progress_list(request):
    if not Permissions.can_view_more_than_own_progress(request.user):
        request.session['error_message']='You are not authorized to view other members\' progress.'
        return redirect('member_resources:index')
    template = loader.get_template('member_resources/progress_list.html')
    context_dict = {
        'progress_profiles':Permissions.profiles_you_can_view(request.user).order_by('status','last_name'),
        'can_manage_actives':Permissions.can_manage_active_progress(request.user),
        'can_manage_electees':Permissions.can_manage_electee_progress(request.user),
        'subnav':'view_others_progress',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def download_active_progress(request):
    if not Permissions.can_manage_active_progress(request.user):
        request.session['error_message']='You are not authorized to view actives\' progress.'
        return redirect('member_resources:index')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename="ActiveProgress.csv"'

    writer = UnicodeWriter(response)
    
    distinctions_actives = DistinctionType.objects.filter(status_type__name="Active").distinct()
    query = Q()
    for distinction in distinctions_actives:
        query = query | Q(distinction_type=distinction)
    query = query & Q(term=get_current_term().semester_type)
    requirements = Requirement.objects.filter(query)
    unflattened_reqs = package_requirements(requirements)
    active_reqs = flatten_reqs(unflattened_reqs)
    progress_rows = []
    active_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Active")
    for profile in active_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        row ={'member':profile,'progress':flatten_progress(packaged_progress,active_reqs)}
        dist_progress = []
        include_in_sheet = False
        for distinction in distinctions_actives.order_by('name'):
            amount_req = 0;
            amount_has = 0;
            for event_category,data in unflattened_reqs.items():
                req = data["requirements"].filter(distinction_type=distinction)
                if req:
                    amount_req_temp=req[0].amount_required
                else:
                    amount_req_temp = 0
                if event_category in packaged_progress:
                    amount_has_temp = packaged_progress[event_category]['sat']
                else:
                    amount_has_temp = 0
                if amount_has_temp >amount_req_temp:
                    amount_has = amount_has + amount_req_temp
                else:
                    amount_has = amount_has + amount_has_temp
                amount_req=amount_req+amount_req_temp
            has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
            close_dist = (amount_has/amount_req)>.75
            dist_progress.append(unicode(has_dist))
            dist_progress.append(unicode(close_dist))
            if amount_has>0:
                include_in_sheet = True
        row["distinctions"]=dist_progress
        if include_in_sheet:
            progress_rows.append(row)
    active_reqs_unicode = []
    for req in active_reqs:
        active_reqs_unicode.append(unicode(req))
    first_row = ['Name','uniqname']+active_reqs_unicode
    for distinction in distinctions_actives.order_by('name'):
        first_row.append('Has '+unicode(distinction)+' status?')
        first_row.append('Is close ?')
    writer.writerow(first_row)
    for row in progress_rows:
        progress_temp = []
        for item in row["progress"]:
            progress_temp.append(unicode(item['sat']))
        row_to_write = [row["member"].get_full_name(),row["member"].uniqname]+progress_temp+row["distinctions"]
        writer.writerow(row_to_write)

    return response

def download_grad_el_progress(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to view electees\' progress.'
        return redirect('member_resources:index')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename="GradElecteeProgress.csv"'

    writer = csv.writer(response)
    distinctions_grad_el = DistinctionType.objects.filter(status_type__name="Electee").filter(standing_type__name="Graduate").distinct()
    query = Q()
    for distinction in distinctions_grad_el:
        query = query | Q(distinction_type=distinction)
    query = query & Q(term=get_current_term().semester_type)
    requirements = Requirement.objects.filter(query)
    unflattened_reqs = package_requirements(requirements)
    grad_electees_reqs = flatten_reqs(unflattened_reqs)
    progress_rows_grad_el = []
    grad_el_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Electee").filter(standing__name="Graduate")
    for profile in grad_el_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        row ={'member':profile,'progress':flatten_progress(packaged_progress,grad_electees_reqs)}
        dist_progress = []
        for distinction in distinctions_grad_el.order_by('name'):
            amount_req = 0;
            amount_has = 0;
            for event_category,data in unflattened_reqs.items():
                req = data["requirements"].filter(distinction_type=distinction)
                if req:
                    amount_req_temp=req[0].amount_required
                else:
                    amount_req_temp = 0
                if event_category in packaged_progress:
                    amount_has_temp = packaged_progress[event_category]['full']
                else:
                    amount_has_temp = 0
                if amount_has_temp >amount_req_temp:
                    amount_has = amount_has + amount_req_temp
                else:
                    amount_has = amount_has + amount_has_temp
                amount_req=amount_req+amount_req_temp
            has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
            close_dist = (amount_has/amount_req)>.75
            dist_progress.append(has_dist)
            dist_progress.append(close_dist)
        row["distinctions"]=dist_progress
        progress_rows_grad_el.append(row)
    first_row = ['Name','uniqname']+grad_electees_reqs
    for distinction in distinctions_grad_el.order_by('name'):
        first_row.append('Has '+unicode(distinction)+' status?')
        first_row.append('Is close ?')
    writer.writerow(first_row)
    for row in progress_rows_grad_el:
        progress_temp = []
        for item in row["progress"]:
            progress_temp.append(item['full'])
        row_to_write = [row["member"].get_full_name(),row["member"].uniqname]+progress_temp+row["distinctions"]
        writer.writerow(row_to_write)

    return response
def download_ugrad_el_progress(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to view electees\' progress.'
        return redirect('member_resources:index')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename="UndergradElecteeProgress.csv"'

    writer = csv.writer(response)
    distinctions_ugrad_el = DistinctionType.objects.filter(status_type__name="Electee").filter(standing_type__name="Undergraduate").distinct()
    query = Q()
    for distinction in distinctions_ugrad_el:
        query = query | Q(distinction_type=distinction)
    query = query & Q(term=get_current_term().semester_type)
    requirements = Requirement.objects.filter(query)
    unflattened_reqs = package_requirements(requirements)
    ugrad_electees_reqs = flatten_reqs(unflattened_reqs)
    progress_rows_ugrad_el = []
    ugrad_el_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Electee").filter(standing__name="Undergraduate")
    for profile in ugrad_el_profiles:
        packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
        row ={'member':profile,'progress':flatten_progress(packaged_progress,ugrad_electees_reqs)}
        dist_progress = []
        for distinction in distinctions_ugrad_el.order_by('name'):
            amount_req = 0;
            amount_has = 0;
            for event_category,data in unflattened_reqs.items():
                req = data["requirements"].filter(distinction_type=distinction)
                if req:
                    amount_req_temp=req[0].amount_required
                else:
                    amount_req_temp = 0
                if event_category in packaged_progress:
                    amount_has_temp = packaged_progress[event_category]['full']
                else:
                    amount_has_temp = 0
                if amount_has_temp >amount_req_temp:
                    amount_has = amount_has + amount_req_temp
                else:
                    amount_has = amount_has + amount_has_temp
                amount_req=amount_req+amount_req_temp
            has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
            close_dist = (amount_has/amount_req)>.75
            dist_progress.append(has_dist)
            dist_progress.append(close_dist)
        row["distinctions"]=dist_progress
        progress_rows_ugrad_el.append(row)
    first_row = ['Name',"uniqname"]+ugrad_electees_reqs
    for distinction in distinctions_ugrad_el.order_by('name'):
        first_row.append('Has '+unicode(distinction)+' status?')
        first_row.append('Is close ?')
    writer.writerow(first_row)
    for row in progress_rows_ugrad_el:
        progress_temp = []
        for item in row["progress"]:
            progress_temp.append(item['full'])
        row_to_write = [row["member"].get_full_name(),row["member"].uniqname]+progress_temp+row["distinctions"]
        writer.writerow(row_to_write)

    return response
def view_progress_table(request):
    can_manage_actives = Permissions.can_manage_active_progress(request.user)
    can_manage_electees= Permissions.can_manage_electee_progress(request.user)
    if not (can_manage_actives or can_manage_electees):
        request.session['error_message']='You are not authorized to view members\' progress.'
        return redirect('member_resources:index')
    if can_manage_actives:
        distinctions_actives = DistinctionType.objects.filter(status_type__name="Active").distinct().order_by('name')
        query = Q()
        for distinction in distinctions_actives:
            query = query | Q(distinction_type=distinction)
        query = query & Q(term=get_current_term().semester_type)
        requirements = Requirement.objects.filter(query)
        unflattened_reqs = package_requirements(requirements)
        active_reqs = flatten_reqs(unflattened_reqs)
        progress_rows = []
        active_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Active")
        for profile in active_profiles:
            packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
            category_hours = get_events_signed_up_hours(profile.uniqname)
            packaged_future_progress=package_future_progress(packaged_progress,category_hours)
            row ={'member':profile,'progress':flatten_progress(packaged_progress,active_reqs),'future_progress':flatten_progress(packaged_future_progress,active_reqs)}
            merged_progress = []
            for count in range(len(row['progress'])):
                merged_progress.append({'has':row['progress'][count],'will_have':row['future_progress'][count]})
            row['merged']=merged_progress
            dist_progress = []
            for distinction in distinctions_actives:
                amount_req = 0;
                amount_has = 0;
                for event_category,data in unflattened_reqs.items():
                    req = data["requirements"].filter(distinction_type=distinction)
                    if req:
                        amount_req_temp=req[0].amount_required
                    else:
                        amount_req_temp = 0
                    if event_category in packaged_progress:
                        amount_has_temp = packaged_progress[event_category]['sat']
                    else:
                        amount_has_temp = 0
                    if amount_has_temp >amount_req_temp:
                        amount_has = amount_has + amount_req_temp
                    else:
                        amount_has = amount_has + amount_has_temp
                    amount_req=amount_req+amount_req_temp
                has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
                close_dist = (Decimal(1.0)*amount_has)/amount_req>.75
                dist_progress.append(has_dist)
                dist_progress.append(close_dist)

            row["distinctions"]=dist_progress
            progress_rows.append(row)
    else:
        active_reqs=None
        progress_rows=None
        distinctions_actives = None
    if can_manage_electees:
        #ugrad
        distinctions_ugrad_el = DistinctionType.objects.filter(status_type__name="Electee").filter(standing_type__name="Undergraduate").distinct().order_by('name')
        query = Q()
        for distinction in distinctions_ugrad_el:
            query = query | Q(distinction_type=distinction)
        query = query & Q(term=get_current_term().semester_type)
        requirements = Requirement.objects.filter(query)
        unflattened_reqs = package_requirements(requirements)
        ugrad_electees_reqs = flatten_reqs(unflattened_reqs)
        progress_rows_ugrad_el = []
        ugrad_el_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Electee").filter(standing__name="Undergraduate")
        for profile in ugrad_el_profiles:
            packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
            category_hours = get_events_signed_up_hours(profile.uniqname)
            packaged_future_progress=package_future_progress(packaged_progress,category_hours)
            row ={'member':profile,'progress':flatten_progress(packaged_progress,ugrad_electees_reqs),'future_progress':flatten_progress(packaged_future_progress,ugrad_electees_reqs)}
            merged_progress = []
            for count in range(len(row['progress'])):
                merged_progress.append({'has':row['progress'][count],'will_have':row['future_progress'][count]})
            row['merged']=merged_progress
            dist_progress = []
            for distinction in distinctions_ugrad_el.order_by('name'):
                amount_req = 0;
                amount_has = 0;
                for event_category,data in unflattened_reqs.items():
                    req = data["requirements"].filter(distinction_type=distinction)
                    if req:
                        amount_req_temp=req[0].amount_required
                    else:
                        amount_req_temp = 0
                    if event_category in packaged_progress:
                        amount_has_temp = packaged_progress[event_category]['full']
                    else:
                        amount_has_temp = 0
                    if amount_has_temp >amount_req_temp:
                        amount_has = amount_has + amount_req_temp
                    else:
                        amount_has = amount_has + amount_has_temp
                    amount_req=amount_req+amount_req_temp
                has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
                close_dist = (Decimal(1.0)*amount_has/amount_req)>.75
                dist_progress.append(has_dist)
                dist_progress.append(close_dist)

            row["distinctions"]=dist_progress
            progress_rows_ugrad_el.append(row)
        #grad
        distinctions_grad_el = DistinctionType.objects.filter(status_type__name="Electee").filter(standing_type__name="Graduate").distinct().order_by('name')
        query = Q()
        for distinction in distinctions_grad_el:
            query = query | Q(distinction_type=distinction)
        query = query & Q(term=get_current_term().semester_type)
        requirements = Requirement.objects.filter(query)
        unflattened_reqs = package_requirements(requirements)
        grad_electees_reqs = flatten_reqs(unflattened_reqs)
        progress_rows_grad_el = []
        grad_el_profiles = Permissions.profiles_you_can_view(request.user).filter(status__name="Electee").filter(standing__name="Graduate")
        for profile in grad_el_profiles:
            packaged_progress = package_progress(ProgressItem.objects.filter(member=profile,term=get_current_term()))
            category_hours = get_events_signed_up_hours(profile.uniqname)
            packaged_future_progress=package_future_progress(packaged_progress,category_hours)
            row ={'member':profile,'progress':flatten_progress(packaged_progress,grad_electees_reqs),'future_progress':flatten_progress(packaged_future_progress,grad_electees_reqs)}
            merged_progress = []
            for count in range(len(row['progress'])):
                merged_progress.append({'has':row['progress'][count],'will_have':row['future_progress'][count]})
            row['merged']=merged_progress
            dist_progress = []
            for distinction in distinctions_grad_el.order_by('name'):
                amount_req = 0;
                amount_has = 0;
                for event_category,data in unflattened_reqs.items():
                    req = data["requirements"].filter(distinction_type=distinction)
                    if req:
                        amount_req_temp=req[0].amount_required
                    else:
                        amount_req_temp = 0
                    if event_category in packaged_progress:
                        amount_has_temp = packaged_progress[event_category]['full']
                    else:
                        amount_has_temp = 0
                    if amount_has_temp >amount_req_temp:
                        amount_has = amount_has + amount_req_temp
                    else:
                        amount_has = amount_has + amount_has_temp
                    amount_req=amount_req+amount_req_temp
                has_dist = has_distinction_met(packaged_progress,distinction,unflattened_reqs)
                close_dist = (Decimal(1.0)*amount_has)>(.75*amount_req)
                dist_progress.append(has_dist)
                dist_progress.append(close_dist)

            row["distinctions"]=dist_progress
            progress_rows_grad_el.append(row)
    else:
        ugrad_electees_reqs=None
        progress_rows_ugrad_el =None
        distinctions_ugrad_el =None
        grad_electees_reqs=None
        progress_rows_grad_el =None
        distinctions_grad_el =None
    template = loader.get_template('member_resources/progress_table.html')
    context_dict = {
        'progress_profiles':Permissions.profiles_you_can_view(request.user),
        'can_manage_actives':can_manage_actives,
        'can_manage_electees':can_manage_electees,
        'can_manage_actives':Permissions.can_manage_active_progress(request.user),
        'can_manage_electees':Permissions.can_manage_electee_progress(request.user),
        'active_reqs':active_reqs,
        'progress_rows':progress_rows,
        'distinctions_actives':distinctions_actives,
        'ugrad_electees_reqs':ugrad_electees_reqs,
        'progress_rows_ugrad_el':progress_rows_ugrad_el,
        'grad_electees_reqs':grad_electees_reqs,
        'progress_rows_grad_el':progress_rows_grad_el,
        'distinction_ugrad_el':distinctions_ugrad_el,
        'distinction_grad_el':distinctions_grad_el,
        'subnav':'view_others_progress',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def get_minutes_view(request,meeting_type, meeting_type_name):
    request.session['current_page']=request.path
    today = date.today()
    minutes    = MeetingMinutes.objects.filter(meeting_type=meeting_type)
    template = loader.get_template('member_resources/minutes.html')
    context_dict = {
        'minutes':minutes,
        'minutes_name':meeting_type_name,
        'can_upload_minutes':Permissions.can_upload_minutes(request.user),
        'user_is_member':user_is_member(request.user),
        'subnav':'history',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
   
def officer_meeting_minutes(request):
    if not user_is_member(request.user):
        request.session['error_message']='You are not authorized to view this page'
        return redirect('member_resources:index')
    return get_minutes_view(request,'OF','Officer Meeting Minutes')
def advisory_board_meeting_minutes(request):
    if not user_is_member(request.user):
        request.session['error_message']='You are not authorized to view this page'
        return redirect('member_resources:index')
    return get_minutes_view(request,'AD','Advisory Board Minutes')
def main_meeting_minutes(request):
    return get_minutes_view(request,'MM','Meeting Minutes')
def new_initiatives_meeting_minutes(request):
    return get_minutes_view(request,'NI','New Initiatives Meeting Minutes')


def upload_minutes(request):
    if not Permissions.can_upload_minutes(request.user):
        request.session['error_message']='You are not authorized to upload minutes.'
        return redirect('member_resources:index')
    if request.method == 'POST':
        form = MeetingMinutesForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            request.session['success_message']='Minutes uploaded successfully'
            return get_previous_page(request,'member_resources:officer_meeting_minutes')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        form = MeetingMinutesForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'history',
        'has_files':True,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Upload Minutes',
        'back_button':{'link':reverse('member_resources:main_meeting_minutes'),'text':'To Meeting Minutes'},
        'form_title':'Upload Meeting Minutes',
        'help_text':'Please make sure to choose the correct meeting type.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def project_reports_list(request):
    if not Permissions.can_access_project_reports(request.user):
        request.session['error_message']='You are not authorized to view/edit project reports'
        return redirect('member_resources:index')
    project_reports = Permissions.project_reports_you_can_view(request.user)
    
    events_w_o_reports = None
    pending_events=None
    if Permissions.can_view_missing_reports(request.user):
        events_w_o_reports = get_events_w_o_reports(get_current_term())
    if Permissions.can_view_pending_events(request.user):
        pending_events=get_pending_events()
    template = loader.get_template('member_resources/list_project_reports.html')
    context_dict = {
        'project_reports':project_reports,
        'pending_events':pending_events,
        'events_w_o_reports':events_w_o_reports,
        'subnav':'history',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))




def access_history(request):    
    if not (Permissions.can_access_history(request.user)):
        request.session['error_message']='You are not authorized to access reports/history.'
        return redirect('member_resources:index')

    template = loader.get_template('member_resources/manage_reports.html')
    context_dict = {
        'can_view_feedback':Permissions.can_view_meeting_feedback(request.user),
        'can_access_project_reports':Permissions.can_access_project_reports(request.user),
        'can_create_nep':Permissions.can_create_events(request.user),
        'subnav':'history',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
        
def view_misc_reqs(request):    
    if not (Permissions.can_change_requirements(request.user) or Permissions.can_manage_misc_reqs(request.user)):
        request.session['error_message']='You are not authorized to manage requirements.'
        return redirect('member_resources:index')

    template = loader.get_template('member_resources/manage_misc_reqs.html')
    current_term = get_current_term()
    if current_term.semester_type.name=='Summer':
        current_term = get_next_term(current_term)
    next_term = get_next_full_term(current_term)
    context_dict = {
        'can_add_electee_members':Permissions.can_add_electee_members(request.user),
        'can_manage_project_leaders':Permissions.can_manage_project_leaders(request.user),
        'can_manage_officers':Permissions.can_manage_officers(request.user),
        'terms':AcademicTerm.objects.all().exclude(semester_type__name='Summer').exclude(id=current_term.id).exclude(id=next_term.id).order_by('-year','-semester_type'),
        'current_term':current_term,
        'next_term':next_term,
        'can_manage_actives':Permissions.can_manage_active_progress(request.user),
        'can_manage_electees':Permissions.can_manage_electee_progress(request.user),
        'can_manage_finances':Permissions.can_manage_finances(request.user),
        'can_approve_tutoring':Permissions.can_approve_tutoring(request.user),
        'can_manage_ugrad_paperwork':Permissions.can_manage_ugrad_paperwork(request.user),
        'can_manage_grad_paperwork':Permissions.can_manage_grad_paperwork(request.user),
        'can_change_requirements':Permissions.can_change_requirements(request.user),
        'can_manage_misc_reqs':Permissions.can_manage_misc_reqs(request.user),
        'can_add_leadership_credit':Permissions.can_add_leadership_credit(request.user),
        'can_add_external_service':Permissions.can_add_external_service(request.user),
        'can_change_active_reqs':Permissions.can_change_active_requirements(request.user),
        'can_change_ugrad_electee_reqs':Permissions.can_change_ugrad_electee_requirements(request.user),
        'can_change_grad_electee_reqs':Permissions.can_change_grad_electee_requirements(request.user),
        'can_manage_actives':Permissions.can_manage_active_progress(request.user),
        'can_manage_interviews':(Permissions.can_manage_active_progress(request.user) or Permissions.can_manage_electee_progress(request.user)),
        'active_distinctions':DistinctionType.objects.filter(status_type__name="Active"),
        'ugrad_electee_distinctions':DistinctionType.objects.filter(status_type__name="Electee", standing_type__name="Undergraduate"),
        'grad_electee_distinctions':DistinctionType.objects.filter(status_type__name="Electee",standing_type__name="Graduate"),
        'subnav':'misc_reqs',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_website(request):    
    if not Permissions.can_manage_website(request.user):
        request.session['error_message']='You are not authorized to manage the website.'
        return redirect('member_resources:index')

    template = loader.get_template('member_resources/manage_website.html')
    term = get_current_term()
    next_term = get_next_term(term)
    today = date.today() 
    should_warn = True
    HomePageSlideShowFormSet = modelformset_factory(SlideShowPhoto,can_delete=True)
    if request.method =='POST':
        formset = HomePageSlideShowFormSet(request.POST,request.FILES,prefix='slideshow')
        if formset.is_valid():
            formset.save()
            request.session['success_message']='Home Page Slideshow updated successfully.'
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = HomePageSlideShowFormSet(prefix='slideshow')
    if term.semester_type.name=='Fall':
        if term.year == today.year and today.month==12:
            should_warn=False
        elif term.year+1 == today.year and today.month ==1:
            should_warn=False
    elif term.semester_type.name=='Summer':
        if term.year == today.year and (today.month==8 or today.month ==9):
            should_warn=False
    elif term.semester_type.name=='Winter':
        if term.year == today.year and (today.month==4 or today.month ==5):
            should_warn=False
    context_dict = {
        'can_change_term':Permissions.can_change_website_term(request.user),
        'warn_about_change':should_warn,
        'term':term,
        'next_term':next_term,
        'formset':formset,
        'prefix':'slideshow',
        'subnav':'website',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def advance_term(request):
    if not Permissions.can_change_website_term(request.user):
        request.session['error_message']='You are not authorized to manage the website.'
        return redirect('member_resources:index')

    current_terms = CurrentTerm.objects.all()
    if current_terms.count()!=1:
        raise IntegrityError('There must be one and only one current term, inspect the database as there are %d current terms'%(current_terms.count()))
    term = get_current_term()
    next_term = get_next_term(term)
    c=current_terms[0]
    c.current_term = next_term
    c.save()
    return redirect('member_resources:manage_website')

#def manage_membership(request):    
#    if not Permissions.can_manage_membership(request.user):
#        request.session['error_message']='You are not authorized to manage users.'
#        return redirect('member_resources:index')
#
#    template = loader.get_template('member_resources/manage_membership.html')
#    current_term = get_current_term()
#    if current_term.semester_type.name=='Summer':
#        current_term = get_next_term(current_term)
#    next_term = get_next_full_term(current_term)
#    context_dict = {
#        'can_add_electee_members':Permissions.can_add_electee_members(request.user),
#        'can_manage_project_leaders':Permissions.can_manage_project_leaders(request.user),
#        'can_manage_officers':Permissions.can_manage_officers(request.user),
#        'terms':AcademicTerm.objects.all().exclude(semester_type__name='Summer').exclude(id=current_term.id).exclude(id=next_term.id).order_by('-year','-semester_type'),
#        'current_term':current_term,
#        'next_term':next_term,
#        'can_manage_actives':Permissions.can_manage_active_progress(request.user),
#        'can_manage_electees':Permissions.can_manage_electee_progress(request.user),
#        'subnav':'manage_members',
#        }
#    context_dict.update(get_common_context(request))
#    context_dict.update(get_permissions(request.user))
#    context = RequestContext(request, context_dict)
#    return HttpResponse(template.render(context))

def manage_officers(request,term_id):    
    if not Permissions.can_manage_officers(request.user):
        request.session['error_message']='You are not authorized to manage chapter officers.'
        return redirect('member_resources:index')
    ManageOfficersFormSet = modelformset_factory(Officer,exclude=('term',))
    term =get_object_or_404(AcademicTerm,id=term_id)
    if request.method =='POST':
        formset = ManageOfficersFormSet(request.POST,request.FILES,prefix='officers',queryset=Officer.objects.filter(term=term))
        if formset.is_valid():
            formset.save()
            for instance in formset.new_objects:
                instance.term = [term]
                instance.save()
            request.session['success_message']='Officers updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = ManageOfficersFormSet(prefix='officers',queryset=Officer.objects.filter(term=term))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'officers',
        'subnav':'misc_reqs',
        'can_add_row':True,
        'has_files':True,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Officers',
        'form_title':'Add/Remove Members as Officers for %s'%(unicode(term)),
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def add_electee_DA_PA_status(request):   
    if not Permissions.can_manage_active_progress(request.user):
        request.session['error_message']='You are not authorized to manage electee DA/PA status.'
        return redirect('member_resources:index')
    term = get_current_term()
    if request.method =='POST':
        formset = ManageElecteeDAPAFormSet(request.POST,prefix='current_status')
        if formset.is_valid():
            formset.save(commit=False)
            for instance in formset.new_objects:
                if instance:
                    instance.term = term
                    if 'DA' in instance.distinction_type.name:
                        instance.distinction_type=DistinctionType.objects.get(name='Distinguished Active')
                    elif 'PA' in instance.distinction_type.name:
                        instance.distinction_type=DistinctionType.objects.get(name='Prestigious Active')
                    if not Distinction.objects.filter(member=instance.member,distinction_type=instance.distinction_type,term=term).exists():
                        instance.save()
            request.session['success_message']='Active Statuses Updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial=[]
        #electee DA
        for distinction in DistinctionType.objects.filter(status_type__name="Electee").filter(name__contains='DA'):
            related_distinction = DistinctionType.objects.get(name='Distinguished Active')
            electees_already_received_distinction = MemberProfile.objects.filter(distinction__distinction_type=related_distinction,distinction__term=get_current_term())
            electees = get_electees_with_status(distinction)
            for electee in electees:
                if electee in electees_already_received_distinction:
                    continue
                gift='Not specified'
                initial.append({'member':electee,'distinction_type':distinction,'gift':gift})
        for distinction in DistinctionType.objects.filter(status_type__name="Electee").filter(name__contains='PA'):
            related_distinction = DistinctionType.objects.get(name='Prestigious Active')
            electees_already_received_distinction = MemberProfile.objects.filter(distinction__distinction_type=related_distinction,distinction__term=get_current_term())
            electees = get_electees_with_status(distinction)
            for electee in electees:
                if electee in electees_already_received_distinction:
                    continue
                gift='Not specified'
                initial.append({'member':electee,'distinction_type':distinction,'gift':gift})
        ManageElecteeDAPAFormSet.extra=len(initial)+1
        formset = ManageElecteeDAPAFormSet(queryset=Distinction.objects.none(),initial=initial,prefix='current_status')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'current_status',
        'subnav':'misc_reqs',
        'can_add_row':True,
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Statuses',
        'form_title':'Add Electee DA/PA Distinctions for  %s'%(unicode(term)),
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        'help_text':'This list is pre-populated with members who have enough credit on the website to receive the noted status. Members whose status has already been logged are omitted.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def add_active_statuses(request):   
    if not Permissions.can_manage_active_progress(request.user):
        request.session['error_message']='You are not authorized to manage active members.'
        return redirect('member_resources:index')
    term = get_current_term()
    if request.method =='POST':
        formset = ManageActiveCurrentStatusFormSet(request.POST,prefix='current_status')
        if formset.is_valid():
            formset.save(commit=False)
            for instance in formset.new_objects:
                if instance:
                    instance.term = term
                    if not Distinction.objects.filter(member=instance.member,distinction_type=instance.distinction_type,term=term).exists():
                        instance.save()
            request.session['success_message']='Active Statuses Updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial=[]
        for distinction in DistinctionType.objects.filter(status_type__name="Active"):
            actives_already_received_distinction = MemberProfile.objects.filter(distinction__distinction_type=distinction,distinction__term=get_current_term())
            actives = get_actives_with_status(distinction)
            for active in actives:
                if active in actives_already_received_distinction:
                    continue
                if distinction.name=='Active':
                    gift='N/A'
                else:
                    gift='Not specified'
                initial.append({'member':active,'distinction_type':distinction,'gift':gift})
        ManageActiveCurrentStatusFormSet.extra=len(initial)+1
        formset = ManageActiveCurrentStatusFormSet(queryset=Distinction.objects.none(),initial=initial,prefix='current_status')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'current_status',
        'subnav':'misc_reqs',
        'can_add_row':True,
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Statuses',
        'form_title':'Add Active Distinctions for  %s'%(unicode(term)),
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        'help_text':'This list is pre-populated with members who have enough credit on the website to receive the noted status. Members whose status has already been logged are omitted.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_active_statuses(request):   
    if not Permissions.can_manage_active_progress(request.user):
        request.session['error_message']='You are not authorized to manage active progress.'
        return redirect('member_resources:index')
    ManageActiveCurrentStatusFormSet = modelformset_factory(Distinction,can_delete=True)
    ManageActiveCurrentStatusFormSet.form.base_fields['member'].queryset=get_actives()
    ManageActiveCurrentStatusFormSet.form.base_fields['distinction_type'].queryset=DistinctionType.objects.filter(status_type__name='Active')
    if request.method =='POST':
        formset = ManageActiveCurrentStatusFormSet(request.POST,prefix='active_status')
        if formset.is_valid():
            formset.save()
            request.session['success_message']='Active statuses updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = ManageActiveCurrentStatusFormSet(prefix='active_status')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'active_status',
        'subnav':'misc_reqs',
        'can_add_row':True,
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Statuses',
        'form_title':'Edit Active Distinctions',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        'help_text':'This list contains members\' status that have already been logged. You may edit or remove any status listed here. You may also add new statuses, but if for the current term, the \'Add Active/DA/PA Status \' tool is recommended.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

# Do not point a url directly at this
def add_to_list(request,type_of_list):
    error_lists={'bad_uniqnames':[],'current_actives':[],'current_electees':[]}
    current_actives = ActiveList.objects.all()
    current_electees_ugrad = UndergradElecteeList.objects.all()
    current_electees_grad = GradElecteeList.objects.all()
    if request.method == 'POST':
        form = MassAddProjectLeadersForm(request.POST,prefix='mass-add')
        if form.is_valid():
            uniqnames=form.cleaned_data['uniqnames'].split('\n')
            expr=re.compile('^[a-z]{3,8}$')
            for uniqname in uniqnames:
                uniqname_stripped = uniqname.strip()
                if not expr.match(uniqname_stripped):
                    error_lists['bad_uniqnames'].append(uniqname_stripped)
                    continue
                if current_actives.filter(uniqname=uniqname_stripped).exists():
                    error_lists['current_actives'].append(uniqname_stripped)
                    continue
                if current_electees_ugrad.filter(uniqname=uniqname_stripped).exists() or current_electees_grad.filter(uniqname=uniqname_stripped).exists():
                    error_lists['current_electees'].append(uniqname_stripped)
                    continue
                if type_of_list == 'Actives':
                    a = ActiveList(uniqname=uniqname_stripped)
                elif type_of_list =='Undergrad Electees':
                    a = UndergradElecteeList(uniqname=uniqname_stripped)
                else:
                    a = GradElecteeList(uniqname=uniqname_stripped)
                a.save()
            if not (error_lists['bad_uniqnames'] or error_lists['current_actives'] or error_lists['current_electees']):
                request.session['success_message']='All uniqnames added successfully'
                return redirect('member_resources:view_misc_reqs')
            else:
                request.session['warning_message']='Some uniqnames were not added'
                form=MassAddProjectLeadersForm(initial={'uniqnames':'\n'.join(error_lists['bad_uniqnames']+error_lists['current_actives']+error_lists['current_electees'])},prefix='mass-add')
    else:
        form = MassAddProjectLeadersForm(prefix='mass-add')

    if type_of_list == 'Actives':
        current_list = current_actives
        is_active_list = True
        link = reverse('member_resources:add_to_active_list')
    elif type_of_list =='Undergrad Electees':
        current_list = current_electees_ugrad
        is_active_list = False
        link = reverse('member_resources:add_to_ugrad_electee_list')
    else:
        current_list = current_electees_grad
        is_active_list = False
        link = reverse('member_resources:add_to_grad_electee_list')
    template = loader.get_template('member_resources/add_to_member_list.html')
    context_dict = {
        'mass_form':form,
        'error_lists':error_lists,
        'current_list':current_list,
        'is_active_list':is_active_list,
        'list_name':type_of_list,
        'link':link,
        'subnav':'misc_reqs',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def add_to_active_list(request):
    if not Permissions.can_manage_active_progress(request.user):
        request.session['error_message']='You are not authorized to manage active members.'
        return redirect('member_resources:index')
    return add_to_list(request,'Actives')
def add_to_ugrad_electee_list(request):
    if not Permissions.can_add_electee_members(request.user):
        request.session['error_message']='You are not authorized to manage electees.'
        return redirect('member_resources:index')
    return add_to_list(request,'Undergrad Electees')
def add_to_grad_electee_list(request):
    if not Permissions.can_add_electee_members(request.user):
        request.session['error_message']='You are not authorized to manage electees.'
        return redirect('member_resources:index')
    return add_to_list(request,'Grad Electees')
def add_leadership_credit(request):
    if not Permissions.can_add_leadership_credit(request.user):
        request.session['error_message']='You are not authorized to manage leadership credit.'
        return redirect('member_resources:index')
    error_list=[]
    term = get_current_term()
    leadership_category = EventCategory.objects.get(name='Leadership')
    if request.method == 'POST':
        if 'submit' in request.POST:
            formset = LeadershipCreditFormSet(request.POST,queryset=ProgressItem.objects.none(),prefix='leadership')
            form = MassAddProjectLeadersForm(request.POST,prefix='mass-add')
            if formset.is_valid():
                formset.save(commit=False)
                for instance in formset.new_objects:
                    if not instance or ProgressItem.objects.filter(member=instance.member,term=term,event_type=leadership_category).exists():
                        continue
                    instance.term = term
                    instance.event_type=leadership_category
                    instance.amount_completed = 1
                    instance.date_completed = date.today() 
                    instance.save()
                request.session['success_message']='Leadership credits added successfully'
                return redirect('member_resources:view_misc_reqs')
            else:
                request.session['error_message']=INVALID_FORM_MESSAGE
        elif 'mass-add' in request.POST:
            form = MassAddProjectLeadersForm(request.POST,prefix='mass-add')
            formset = LeadershipCreditFormSet(request.POST,prefix='leadership')
            if form.is_valid():
                uniqnames=form.cleaned_data['uniqnames'].split('\n')
                for uniqname in uniqnames:
                    members = MemberProfile.objects.filter(uniqname=uniqname.strip())
                    if members:
                        if ProgressItem.objects.filter(member=members[0],term=term,event_type=leadership_category).exists():
                            continue
                        leadership_credit = ProgressItem(member=members[0],event_type=leadership_category,date_completed=date.today(),amount_completed=1,term=get_current_term(),name='Leadership Credit')
                        leadership_credit.save()
                    else:
                        error_list.append(uniqname)
                if not error_list:
                    request.session['success_message']='Leadership credit added for all uniqnames'
                    return redirect('member_resources:view_misc_reqs')
                else:
                    request.session['warning_message']='Not all leadership credits added.'
                    form=MassAddProjectLeadersForm(initial={'uniqnames':'\n'.join(error_list)},prefix='mass-add')
                    formset = LeadershipCreditFormSet(request.POST,prefix='leadership')
    else:
        initial=[]
        group_leaders = get_current_group_leaders()
        event_leaders = get_current_event_leaders()
        officers = get_current_officers()
        leader_list = group_leaders |event_leaders |officers
        for leader in leader_list:
            if ProgressItem.objects.filter(member=leader,term=term,event_type=leadership_category).exists():
                continue
            if leader in officers:
                name_str = 'Was an officer'
            elif leader in group_leaders:
                name_str = 'Was a group leader'
            else:
                name_str = 'Led a project'
            initial.append({'member':leader,'name':name_str})
        LeadershipCreditFormSet.extra = len(initial)+1
        formset = LeadershipCreditFormSet(queryset=ProgressItem.objects.none(),initial=initial,prefix='leadership')
        form = MassAddProjectLeadersForm(prefix='mass-add')
    template = loader.get_template('member_resources/add_leadership_credit.html')
    context_dict = {
        'formset':formset,
        'mass_form':form,
        'error_list':error_list,
        'prefix':'leadership',
        'subnav':'misc_reqs',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def handle_electees_stopping_electing(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to remove electees.'
        return redirect('member_resources:index')
    if request.method ==  'POST':
        formset = ManageElecteeStillElecting(request.POST)
        if formset.is_valid():
            for form in formset:
                if not 'uniqname' in form.cleaned_data.keys():
                    continue
                uniqname = form.cleaned_data['uniqname']
                profile = MemberProfile.objects.get(uniqname=uniqname)
                if not profile:
                    continue
                still_electing = form.cleaned_data['still_electing']
                if still_electing and not profile.still_electing:
                    profile.still_electing=True
                    profile.save()
                elif not still_electing and profile.still_electing:
                    electee_stopped_electing(profile)

            request.session['success_message']='Electee status successfully updated.'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data = []
        electee_profiles = MemberProfile.objects.filter(status__name='Electee').order_by('standing','last_name')
        for electee in electee_profiles:
            initial_data.append({'electee':electee.get_full_name(),'uniqname':electee.uniqname,'still_electing':electee.still_electing})
        formset = ManageElecteeStillElecting(initial=initial_data)
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'misc_reqs',
        'can_add_row':False,
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Update Electees Still Electing',
        'form_title':'Manage Electees Still Electing',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        'help_text':'To note that an electee is no longer electing, uncheck the \'Still Electing\' Box next to their name/uniqname. This will unsign them up from any future events and will remove them from electee groups. It will also cause them to generally not show up in the list of members on the website. It will not remove them from events that have already been completed or prevent them from signing up in the future.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def move_electees_to_active(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to give electees active status.'
        return redirect('member_resources:index')
    error_list=[]
    #should probably add extra checking here to ensure added members have correct distinction
    term = get_current_term()
    if request.method == 'POST':
        formset = ElecteeToActiveFormSet(request.POST,prefix='electee2active')
        if formset.is_valid():
            instances=formset.save(commit=False)
            #technically should check here that the distinction doesn't already exist...
            for instance in instances:
                if instance:
                    instance.term = term
                    instance.save()
                    instance.member.status =Status.objects.get(name="Active")
                    instance.member.save()
            request.session['success_message']='Selected electees successfully moved to actives'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial=[]
        electees_with_reqs = get_electees_who_completed_reqs()
        for electee in electees_with_reqs:
            initial.append({'member':electee,'distinction_type':DistinctionType.objects.get(Q(status_type__name='Electee',standing_type = electee.standing)&~(Q(name__contains='DA')|Q(name__contains='PA'))),'gift':'None'})
        ElecteeToActiveFormSet.extra = len(initial)+1
        formset = ElecteeToActiveFormSet(queryset=Distinction.objects.none(),initial=initial,prefix='electee2active')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'electee2active',
        'subnav':'misc_reqs',
        'can_add_row':True,
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Move Electees To Actives',
        'form_title':'Move Electees To Actives',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Membership Management'},
        'help_text':'To note that an electee has completed their requirements and been initiated, check the approve box next to his/her name and then click the button at the bottom. This will move the electee from being considered an electee to being considered an active. NOTE: If the electee also completed electee DA/PA status you\'ll need to take note of this as those statuses are only show up for electees.',
        } 
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def manage_project_leaders(request):
    if not Permissions.can_manage_project_leaders(request.user):
        request.session['error_message']='You are not authorized to manage project leaders.'
        return redirect('member_resources:index')
    error_list=[]
    initial=[]
    project_leader_list = ProjectLeaderList.objects.all()
    for leader in project_leader_list:
        initial.append({'member':leader.member_profile,'is_project_leader':True})
    if request.method == 'POST':
        if 'submit' in request.POST:
            formset = ManageProjectLeadersFormSet(request.POST,prefix='project_leaders')
            form = MassAddProjectLeadersForm()
            if formset.is_valid():
                for form in formset:
                    if not 'member' in form.cleaned_data.keys():
                        continue
                    member = form.cleaned_data['member']
                    keep = form.cleaned_data['is_project_leader']
                    existing_list = ProjectLeaderList.objects.filter(member_profile=member)
                    if keep and not existing_list:
                        p=ProjectLeaderList(member_profile=member)
                        p.save()
                    if not keep and existing_list:
                        for e in existing_list:
                            e.delete()
                request.session['success_message']='Project leaders successfully added.'
                return redirect('member_resources:view_misc_reqs')
            else:
                request.session['error_message']=INVALID_FORM_MESSAGE
        elif 'mass-add' in request.POST:
            form = MassAddProjectLeadersForm(request.POST)
            formset = ManageProjectLeadersFormSet(initial=initial,prefix='project_leaders')
            if form.is_valid():
                uniqnames=form.cleaned_data['uniqnames'].split('\n')
                for uniqname in uniqnames:
                    members = MemberProfile.objects.filter(uniqname=uniqname.strip())
                    if members:
                        existing_list = ProjectLeaderList.objects.filter(member_profile=members[0])
                        if not existing_list:
                            initial.append({'member':members[0],'is_project_leader':True})
                            p=ProjectLeaderList(member_profile=members[0])
                            p.save()
                    else:
                        error_list.append(uniqname)
                if not error_list:
                    request.session['success_message']='All project leaders added successfully.'
                    return redirect('member_resources:view_misc_reqs')
                else:
                    request.session['warning_message']='Not all project leaders added.'
                    form=MassAddProjectLeadersForm(initial={'uniqnames':'\n'.join(error_list)})
                    formset = ManageProjectLeadersFormSet(initial=initial,prefix='project_leaders')
    else:
        formset = ManageProjectLeadersFormSet(initial=initial,prefix='project_leaders')
        form = MassAddProjectLeadersForm()
    template = loader.get_template('member_resources/manage_project_leaders.html')
    context_dict = {
        'formset':formset,
        'mass_form':form,
        'error_list':error_list,
        'prefix':'project_leaders',
        'subnav':'misc_reqs',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def add_external_service(request):
    if not Permissions.can_add_external_service(request.user):
        request.session['error_message']='You are not authorized to manage external service hours.'
        return redirect('member_resources:index')
    ExternalServiceFormSet = modelformset_factory(ProgressItem,exclude=('term','date_completed','event_type','related_event'),can_delete=True)
    ExternalServiceFormSet.form.base_fields['member'].queryset=get_electees()
    if request.method ==  'POST':
        formset = ExternalServiceFormSet(request.POST,queryset=ProgressItem.objects.filter(term=get_current_term(),event_type__name='External Service Hours'),prefix='external_service')
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if instance in formset.new_objects:
                    instance.term = get_current_term()
                    instance.date_completed= date.today()
                    instance.event_type=EventCategory.objects.get(name='External Service Hours')
                prev_ext = ProgressItem.objects.filter(member=instance.member,term=instance.term,event_type__name='External Service Hours')
                if not instance in formset.new_objects:
                    prev_ext.filter(~Q(id=instance.id))
                ext_hours=0
                for item in prev_ext:
                    ext_hours+=item.amount_completed
                if instance.amount_completed+ext_hours>5:
                    instance.amount_completed=max(0,5-ext_hours)
                instance.save()

            request.session['success_message']='External service successfully updated.'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset=ExternalServiceFormSet(queryset=ProgressItem.objects.filter(term=get_current_term(),event_type__name='External Service Hours'),prefix='external_service')
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'external_service',
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update External Service Hours',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Add/Update External Service Hours',
        'help_text':'Note that external service hours only count for electees and that a maximum of 5 may be submitted. Any hours over 5 for a given electee will be saturated at 5.',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_dues(request):
    if not Permissions.can_manage_finances(request.user):
        request.session['error_message']='You are not authorized to manage payment of dues.'
        return redirect('member_resources:index')
    if request.method ==  'POST':
        formset = ManageDuesFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if not 'uniqname' in form.cleaned_data.keys():
                    continue
                uniqname = form.cleaned_data['uniqname']
                profile = MemberProfile.objects.get(uniqname=uniqname)
                if not profile:
                    continue
                dues_paid = form.cleaned_data['dues_paid']
                existing_progress = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Dues')
                if not existing_progress:
                    if not dues_paid:
                        continue
                    p = ProgressItem()
                    p.member = profile
                    p.term = get_current_term()
                    p.amount_completed = 1
                    p.date_completed = date.today()
                    p.name = 'Dues Paid'
                    p.event_type = EventCategory.objects.get(name = 'Dues')
                    p.save()
                else:
                    if dues_paid:
                        continue
                    for e in existing_progress:
                        e.delete()
            request.session['success_message']='Dues successfully updated.'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data = []
        electee_profiles = get_electees().order_by('last_name')
        dues_progress = ProgressItem.objects.filter(event_type__name='Dues',term=get_current_term())
        for electee in electee_profiles:
            has_paid_dues = dues_progress.filter(member=electee).exists()
            initial_data.append({'electee':electee.get_full_name(),'uniqname':electee.uniqname,'dues_paid':has_paid_dues})
        formset = ManageDuesFormSet(initial=initial_data)
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Dues Payment',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage Dues Payment',
        'help_text':'When electees pay their initition dues click the checkbox and click submit.',
        'can_add_row':False,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_interview_credit(request):
    if not (Permissions.can_manage_electee_progress(request.user) or Permissions.can_manage_active_progress(request.user)):
        request.session['error_message']='You are not authorized to manage actives\' completion of interview hours'
        return redirect('member_resources:index')
    interview_types = EventCategory.objects.filter(parent_category__name='Conducted Interviews').order_by('name')
    interview_progress={}
    if request.method == 'POST':
        formset = ManageInterviewsFormSet(request.POST,prefix='active_interview')
        if formset.is_valid():
            for form in formset:
                if not 'member' in form.cleaned_data:
                    continue
                member = form.cleaned_data['member']
                if not member in interview_progress:
                    progress_row = {}
                    for interview_type in interview_types:
                        progress_row[interview_type]=0
                    interview_progress[member]=progress_row
                interview_type = form.cleaned_data['interview_type']
                amount = form.cleaned_data['number_of_interviews']
                interview_progress[member][interview_type]+=amount
            for member in interview_progress.keys():
                progress=interview_progress[member]
                first = True
                for interview_type in interview_types:
                    existing_progress = ProgressItem.objects.filter(member=member,term=get_current_term(),event_type=interview_type,name='Interview')
                    existing_progress_extra = ProgressItem.objects.filter(member=member,term=get_current_term(),event_type=interview_type,name='Extra Interview')
                    mult=1
                    if interview_type.name=='Grad Interviews 30':
                        mult=2.0
                    elif interview_type.name=='Grad Interviews 15':
                        mult=4.0
                    if first:
                        if progress[interview_type]:
                            first=False
                        if existing_progress:
                            if progress[interview_type]:
                                progress[interview_type]-=1
                            else:
                                existing_progress.delete()
                            if existing_progress_extra:
                                if progress[interview_type]:
                                    existing_progress_extra[0].amount_completed=progress[interview_type]/mult
                                    existing_progress_extra[0].save()
                                else:
                                    existing_progress_extra.delete()
                            elif progress[interview_type]:
                                p = ProgressItem(member=member,term=get_current_term(),date_completed=date.today(),name='Extra Interview')
                                p.event_type = interview_type
                                p.amount_completed =progress[interview_type]/mult
                                p.save()
                        elif progress[interview_type]:
                            progress[interview_type]-=1
                            p = ProgressItem(member=member,term=get_current_term(),date_completed=date.today(),name='Interview')
                            p.event_type = interview_type
                            p.amount_completed =1
                            p.save()
                            if existing_progress_extra:
                                if progress[interview_type]:
                                    existing_progress_extra[0].amount_completed=progress[interview_type]/mult
                                    existing_progress_extra[0].save()
                                else:
                                    existing_progress_extra.delete()
                            elif progress[interview_type]:
                                p = ProgressItem(member=member,term=get_current_term(),date_completed=date.today(),name='Extra Interview')
                                p.event_type = interview_type
                                p.amount_completed =progress[interview_type]/mult
                                p.save()
                    else:
                        existing_progress.delete()
                        if existing_progress_extra:
                            if progress[interview_type]:
                                existing_progress_extra[0].amount_completed=progress[interview_type]/mult
                                existing_progress_extra[0].save()
                            else:
                                existing_progress_extra.delete()
                        elif progress[interview_type]:
                            p = ProgressItem(member=member,term=get_current_term(),date_completed=date.today(),name='Extra Interview')
                            p.event_type = interview_type
                            p.amount_completed =progress[interview_type]/mult
                            p.save()
            request.session['success_message']='Interview Credit Successfully Updated'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data=[]
        progress_items = ProgressItem.objects.filter(term=get_current_term(),event_type__parent_category__name='Conducted Interviews').order_by('member__last_name','event_type')
        members_w_progress = sorted(list(set([progress_item.member for progress_item in progress_items])))
        for member in members_w_progress:
            progress=progress_items.filter(member=member)
            for interview_type in interview_types:
                hours=0
                member_progress_items = progress.filter(event_type=interview_type)
                for progress_item in member_progress_items:
                    mult=1
                    if progress_item.name=='Interview':
                        mult=1
                    elif progress_item.event_type.name=='Grad Interviews 30':
                        mult=2
                    elif progress_item.event_type.name=='Grad Interviews 15':
                        mult=4
                    hours+=int(progress_item.amount_completed*mult)
                if hours:
                    initial_data.append({'member':member,'interview_type':interview_type,'number_of_interviews':hours})
        formset=ManageInterviewsFormSet(initial=initial_data,prefix='active_interview')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'active_interview',
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Active\'s Interview Credit',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage Active\'s Interview Credit',
        'help_text':'For each active member that participated in electee interviews, please select the type and number of interviews. You should select the number of interviews completed, *not* the number of hours.',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_active_group_meetings(request):
    if not (Permissions.can_manage_electee_progress(request.user) or Permissions.can_manage_active_progress(request.user)):
        request.session['error_message']='You are not authorized to manage actives\' completion of group_meetings'
        return redirect('member_resources:index')
    if request.method ==  'POST':
        formset = ManageActiveGroupMeetingsFormSet(request.POST,prefix='active_group')
        if formset.is_valid():
            for form in formset:
                if not 'member' in form.cleaned_data.keys():
                    continue
                member = form.cleaned_data['member']
                group_meetings = form.cleaned_data['group_meetings']
                existing_group_meetings = ProgressItem.objects.filter(member=member,term=get_current_term(),event_type__name='Group Meetings')
                existing_extra_group_meetings = ProgressItem.objects.filter(member=member,term=get_current_term(),event_type__name='Extra Group Meetings')
                dist=DistinctionType.objects.filter(status_type__name='Electee',standing_type__name='Undergraduate')
                group_meeting_req = Requirement.objects.filter(distinction_type=dist,event_category__name='Group Meetings',term=get_current_term().semester_type)
                if group_meeting_req:
                    amount_group_req = group_meeting_req[0].amount_required
                else:
                    amount_group_req = 0
                if existing_group_meetings:
                    if group_meetings > amount_group_req:
                        if existing_extra_group_meetings:
                            existing_extra_group_meetings[0].amount_completed=(group_meetings-amount_group_req)
                            existing_extra_group_meetings[0].save()
                        else:
                            p = ProgressItem(member=member,term=get_current_term(),amount_completed=(group_meetings-amount_group_req),date_completed=date.today(),name='Extra Group Meetings')
                            p.event_type = EventCategory.objects.get(name='Extra Group Meetings')
                            p.save()
                        group_meetings=amount_group_req
                    elif existing_extra_group_meetings:
                        existing_extra_group_meetings.delete()
                    if group_meetings:
                        existing_group_meetings[0].amount_completed=group_meetings
                        existing_group_meetings[0].save()
                    else:
                        existing_group_meetings.delete()
                else:
                    amt_group_meetings = min(group_meetings,amount_group_req)
                    amt_extra_meetings = max(0,group_meetings-amount_group_req)
                    p = ProgressItem(member=member,term=get_current_term(),amount_completed=amt_group_meetings,date_completed=date.today(),name='Group Meetings')
                    p.event_type = EventCategory.objects.get(name='Group Meetings')
                    p.save()
                    p2 = ProgressItem(member=member,term=get_current_term(),amount_completed=amt_extra_meetings,date_completed=date.today(),name='Extra Group Meetings')
                    p2.event_type = EventCategory.objects.get(name='Extra Group Meetings')
                    p2.save()
            request.session['success_message']='Active Group Meeting Progress updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data = []
        progress_items = ProgressItem.objects.filter(member__status__name='Active',term=get_current_term()).filter(Q(event_type__name='Group Meetings')|Q(event_type__name='Extra Group Meetings'))
        members = list(set([p.member for p in progress_items]))

        for member in members:
            group_meetings=0
            if progress_items.filter(member=member).exists():
                for p in progress_items.filter(member=member):
                    group_meetings+=int(p.amount_completed)
            initial_data.append({'member':member,'group_meetings':group_meetings})
        formset = ManageActiveGroupMeetingsFormSet(initial=initial_data,prefix='active_group')
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'active_group',
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Active\'s Group Meeting Credit',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage Active\'s Group Meeting Credit',
        'help_text':'Give credit for each group meeting that each group leader hosts/attends. Any above the minimum required will count as social events.',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_ugrad_paperwork(request):
    if not Permissions.can_manage_ugrad_paperwork(request.user):
        request.session['error_message']='You are not authorized to manage completion of paperwork.'
        return redirect('member_resources:index')
    if request.method ==  'POST':
        formset = ManageUgradPaperWorkFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if not 'uniqname' in form.cleaned_data.keys():
                    continue
                uniqname = form.cleaned_data['uniqname']
                profile = MemberProfile.objects.get(uniqname=uniqname)
                if not profile:
                    continue
                exam = form.cleaned_data['electee_exam_completed']
                existing_progress_exam = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Electee Exam')
                char_interviews = form.cleaned_data['interviews_completed']
                existing_progress_char_interviews = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Attended Interviews')
                interviews = form.cleaned_data['peer_interviews_completed']
                existing_progress_interviews = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Peer Interviews')
                group_meetings = form.cleaned_data['group_meetings']
                existing_group_meetings = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Group Meetings')
                existing_extra_group_meetings = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Extra Group Meetings')
                essays = form.cleaned_data['character_essays_completed']
                existing_progress_essays = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Essays')
                if existing_progress_exam and not exam:
                    for e in existing_progress_exam:
                        e.delete()
                if not existing_progress_exam and exam:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=1,date_completed=date.today(),name='Electee Exam Completed')
                    p.event_type = EventCategory.objects.get(name='Electee Exam')
                    p.save()
                if existing_progress_interviews:
                    #for now assume only 1
                    existing_progress_interviews[0].amount_completed=interviews
                    existing_progress_interviews[0].save()
                else:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=interviews,date_completed=date.today(),name='Peer Interviews Completed')
                    p.event_type = EventCategory.objects.get(name='Peer Interviews')
                    p.save()
                if existing_progress_essays:
                    #for now assume only 1
                    existing_progress_essays[0].amount_completed=essays
                    existing_progress_essays[0].save()
                else:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=interviews,date_completed=date.today(),name='Character Essays Completed')
                    p.event_type = EventCategory.objects.get(name='Essays')
                    p.save()
                if existing_progress_char_interviews and not char_interviews:
                    for e in existing_progress_char_interviews:
                        e.delete()
                if not existing_progress_char_interviews and char_interviews:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=2,date_completed=date.today(),name='Attended Interviews')
                    p.event_type = EventCategory.objects.get(name='Attended Interviews')
                    p.save()
                dist=DistinctionType.objects.filter(status_type__name='Electee',standing_type__name='Undergraduate')
                group_meeting_req = Requirement.objects.filter(distinction_type=dist,event_category__name='Group Meetings',term=get_current_term().semester_type)
                if group_meeting_req:
                    amount_group_req = group_meeting_req[0].amount_required
                else:
                    amount_group_req = 0
                if existing_group_meetings:
                    if group_meetings > amount_group_req:
                        if existing_extra_group_meetings:
                            existing_extra_group_meetings[0].amount_completed=(group_meetings-amount_group_req)
                            existing_extra_group_meetings[0].save()
                        else:
                            p = ProgressItem(member=profile,term=get_current_term(),amount_completed=(group_meetings-amount_group_req),date_completed=date.today(),name='Extra Group Meetings')
                            p.event_type = EventCategory.objects.get(name='Extra Group Meetings')
                            p.save()
                        group_meetings=amount_group_req
                    elif existing_extra_group_meetings:
                        existing_extra_group_meetings[0].amount_completed=0
                        existing_extra_group_meetings[0].save()
                    existing_group_meetings[0].amount_completed=group_meetings
                    existing_group_meetings[0].save()
                else:
                    amt_group_meetings = min(group_meetings,amount_group_req)
                    amt_extra_meetings = max(0,group_meetings-amount_group_req)
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=amt_group_meetings,date_completed=date.today(),name='Group Meetings')
                    p.event_type = EventCategory.objects.get(name='Group Meetings')
                    p.save()
                    p2 = ProgressItem(member=profile,term=get_current_term(),amount_completed=amt_extra_meetings,date_completed=date.today(),name='Extra Group Meetings')
                    p2.event_type = EventCategory.objects.get(name='Extra Group Meetings')
                    p2.save()
            request.session['success_message']='Electee paperwork updated successfully'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data = []
        electee_profiles = get_electees().filter(standing__name='Undergraduate').order_by('last_name')
        electee_exam_progress = ProgressItem.objects.filter(event_type__name='Electee Exam',term=get_current_term())
        char_interviews_progress = ProgressItem.objects.filter(event_type__name='Attended Interviews',term=get_current_term())
        peer_interview_progress = ProgressItem.objects.filter(event_type__name='Peer Interviews',term=get_current_term())
        essays_progress = ProgressItem.objects.filter(event_type__name='Essays',term=get_current_term())
        existing_group_meetings = ProgressItem.objects.filter(term=get_current_term(),event_type__name='Group Meetings')
        existing_extra_group_meetings = ProgressItem.objects.filter(term=get_current_term(),event_type__name='Extra Group Meetings')

        for electee in electee_profiles:
            exam = electee_exam_progress.filter(member=electee).exists()
            interviews = 0
            essays = 0
            char_interviews = char_interviews_progress.filter(member=electee).exists()
            group_meetings=0
            if existing_group_meetings.filter(member=electee).exists():
                group_meetings+=int(existing_group_meetings.filter(member=electee)[0].amount_completed)
            if existing_extra_group_meetings.filter(member=electee).exists():
                group_meetings+=int(existing_extra_group_meetings.filter(member=electee)[0].amount_completed)
            if peer_interview_progress.filter(member=electee).exists():
                interviews = int(peer_interview_progress.filter(member=electee)[0].amount_completed)
            if essays_progress.filter(member=electee).exists():
                essays = int(essays_progress.filter(member=electee)[0].amount_completed)
            initial_data.append({'electee':electee.get_full_name(),'uniqname':electee.uniqname,'electee_exam_completed':exam,'peer_interviews_completed':interviews,'character_essays_completed':essays,'interviews_completed':char_interviews,'group_meetings':group_meetings})
        formset = ManageUgradPaperWorkFormSet(initial=initial_data)
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Electee Progress',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage Undergraduate Electee Paperwork Progress',
        'help_text':'For managing undergraduate electee progress toward the more miscellaneous of the requirements.',
        'can_add_row':False,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def manage_grad_paperwork(request):
    if not Permissions.can_manage_grad_paperwork(request.user):
        request.session['error_message']='You are not authorized to manage completion of paperwork.'
        return redirect('member_resources:index')
    if request.method ==  'POST':
        formset = ManageGradPaperWorkFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if not 'uniqname' in form.cleaned_data.keys():
                    continue
                uniqname = form.cleaned_data['uniqname']
                profile = MemberProfile.objects.get(uniqname=uniqname)
                if not profile:
                    continue
                advisor_form = form.cleaned_data['advisor_form_completed']
                background_form = form.cleaned_data['educational_background_form_completed']
                existing_progress_advisor_form= ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Advisor Form')
                existing_progress_background_form= ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Educational Background Form')
                char_interviews = form.cleaned_data['interviews_completed']
                existing_progress_char_interviews = ProgressItem.objects.filter(member=profile,term=get_current_term(),event_type__name='Attended Interviews')
                if existing_progress_advisor_form and not advisor_form:
                    for e in existing_progress_advisor_form:
                        e.delete()
                if not existing_progress_advisor_form and advisor_form:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=1,date_completed=date.today(),name='Advisor Form Completed')
                    p.event_type = EventCategory.objects.get(name='Advisor Form')
                    p.save()
                if existing_progress_background_form and not background_form:
                    for e in existing_progress_background_form:
                        e.delete()
                if not existing_progress_background_form and background_form:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=1,date_completed=date.today(),name='Educational Background Form Completed')
                    p.event_type = EventCategory.objects.get(name='Educational Background Form')
                    p.save()
                if existing_progress_char_interviews and not char_interviews:
                    for e in existing_progress_char_interviews:
                        e.delete()
                if not existing_progress_char_interviews and char_interviews:
                    p = ProgressItem(member=profile,term=get_current_term(),amount_completed=1,date_completed=date.today(),name='Attended Interviews')
                    p.event_type = EventCategory.objects.get(name='Attended Interviews')
                    p.save()
            request.session['success_message']='Electee paperwork updated sucessfully.'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial_data = []
        electee_profiles = get_electees().filter(standing__name='Graduate').order_by('last_name')
        advisor_form_progress = ProgressItem.objects.filter(event_type__name='Advisor Form',term=get_current_term())
        background_form_progress = ProgressItem.objects.filter(event_type__name='Educational Background Form',term=get_current_term())
        char_interviews_progress = ProgressItem.objects.filter(event_type__name='Attended Interviews',term=get_current_term())
        for electee in electee_profiles:
            char_interviews = char_interviews_progress.filter(member=electee).exists()
            advisor_form = advisor_form_progress.filter(member=electee).exists()
            background_form = background_form_progress.filter(member=electee).exists()
            initial_data.append({'electee':electee.get_full_name(),'uniqname':electee.uniqname,'advisor_form_completed':advisor_form,'educational_background_form_completed':background_form,'interviews_completed':char_interviews})
        formset = ManageGradPaperWorkFormSet(initial=initial_data)
    
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Electee Progress',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage Graduate Electee Paperwork Progress',
        'help_text':'For managing graduate electee progress toward the more miscellaneous of the requirements.',
        'can_add_row':False,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def change_requirements(request,distinction_id):   
    distinction = get_object_or_404(DistinctionType,id=distinction_id)
    status = distinction.status_type.name
    standings = distinction.standing_type.all()
    if status == "Active":
        if not Permissions.can_change_active_requirements(request.user):
            request.session['error_message']='You are not authorized to change actives\' requirements.'
            return redirect('member_resources:index')
    elif status == "Electee" and standings.filter(name="Undergraduate").exists():
        if not Permissions.can_change_ugrad_electee_requirements(request.user):
            request.session['error_message']='You are not authorized to change electee requirements.'
            return redirect('member_resources:index')
    elif status == "Electee" and standings.filter(name="Graduate").exists():
        if not Permissions.can_change_grad_electee_requirements(request.user):
            request.session['error_message']='You are not authorized to change electee requirements.'
            return redirect('member_resources:index')
    else:
        raise PermissionDenied()

    RequirementFormSet = modelformset_factory(Requirement,exclude=('distinction_type',),can_delete=True)
    if request.method =='POST':
        formset = RequirementFormSet(request.POST,prefix='requirements')
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.distinction_type = distinction
                instance.save()
            formset.save_m2m()
            request.session['success_message']='Requirements updated successfuly.'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = RequirementFormSet(prefix='requirements',queryset=Requirement.objects.filter(distinction_type=distinction))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'requirements',
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Requirements',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Manage %s Requirements'%(unicode(distinction)),
        'help_text':'For adding, changing, or removing requirements.',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def change_event_categories(request):  
    if not Permissions.can_change_requirements(request.user):
        request.session['error_message']='You are not authorized to change requirement categories.'
        return redirect('member_resources:index')
    if request.user.is_superuser:
        EventCategoryFormSet = modelformset_factory(EventCategory,can_delete=True)
    else:
        EventCategoryFormSet = modelformset_factory(EventCategory)
    if request.method =='POST':
        formset = EventCategoryFormSet(request.POST,prefix='categories')
        if formset.is_valid():
            instances = formset.save()
            request.session['success_message']='Event categories successfully updated'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = EventCategoryFormSet(prefix='categories')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'categories',
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Update Event Categories',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Add or Change Event Categories',
        'help_text':'For adding, changing, or removing event categories. Note that removing an event category will remove any requirements, progress items, or events that use that event. Really don\'t do it.',
        'can_add_row':True,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def view_meeting_feedback_for_term(request,term_id):
    if not Permissions.can_view_meeting_feedback(request.user):
        request.session['error_message']='You are not authorized to view the meeting surveys.'
        return redirect('member_resources:index')
    terms = AcademicTerm.objects.filter(id=term_id)
    if not terms.exists():
        term=get_current_term()
    else:
        term=terms[0]
    completed_meetings = CalendarEvent.objects.filter(completed=True,term=term,event_type__name__contains='Meeting Attendance')
    meeting_surveys = MeetingSignInUserData.objects.filter(meeting_data__event__term=term)
    feedback_surveys=[]
    for meeting in completed_meetings:
        feedback_surveys.append({'meeting':meeting,'surveys':MeetingSignInUserData.objects.filter(meeting_data__event=meeting)})
    template = loader.get_template('member_resources/meeting_feedback.html')
    context_dict = {
        'surveys':meeting_surveys,
        'term':term,
        'subnav':'history',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def view_meeting_feedback(request):
    return view_meeting_feedback_for_term(request,get_current_term().id)

def approve_tutoring_forms(request):  
    if not Permissions.can_approve_tutoring(request.user):
        request.session['error_message']='You are not authorized to approve tutoring forms.'
        return redirect('member_resources:index')
    TutoringFormFormSet = modelformset_factory(TutoringRecord,extra=0,can_delete=True)
    if request.method =='POST':
        formset = TutoringFormFormSet(request.POST)
        if formset.is_valid():
            instances = formset.save()
            tutoring_category = EventCategory.objects.get(name__contains='Tutoring')
            for tutoring_record in instances:
                tutoring_credit = ProgressItem(member=tutoring_record.tutor,event_type=tutoring_category, date_completed=tutoring_record.date_tutored,amount_completed=tutoring_record.number_hours,term=get_current_term(),name='One-on-One Tutoring')
                tutoring_credit.save()
            request.session['success_message']='Tutoring Forms successfully updated'
            return redirect('member_resources:view_misc_reqs')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        formset = TutoringFormFormSet(queryset=TutoringRecord.objects.filter(approved=False))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'subnav':'misc_reqs',
        'back_button':{'link':reverse('member_resources:view_misc_reqs'),'text':'To Miscellaneous Requirements'},
        'submit_name':'Approve Tutoring Forms',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Approve or Delete Tutoring Forms',
        'help_text':'These forms are submitted by members after tutoring sessions. They must be approved for credit to be issued.',
        'can_add_row':False,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))


def update_preferences(request):  
    if not hasattr(request.user,'userprofile'):
        request.session['error_message']='You must be logged in and have created a profile to update preferences.'
        return redirect('member_resources:index')
    if request.method =='POST':
        form = PreferenceForm(PREFERENCES,request.POST)
        if form.is_valid():
            UserPreference.objects.filter(user=request.user.userprofile).delete()
            for key,value in form.cleaned_data.items():
                value_name = [d['values'][int(value)] for d in PREFERENCES if d['name']==key][0]
                up = UserPreference(user=request.user.userprofile,preference_type=key,preference_value=value_name)
                up.save()
            request.session['success_message']='Preferences successfully updated (though not really)'
            return redirect('member_resources:profile',request.user.userprofile.uniqname)
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        initial={}
        users_prefs = UserPreference.objects.filter(user=request.user.userprofile)
        for preference in PREFERENCES:
            this_pref = users_prefs.filter(preference_type=preference['name'])
            if this_pref.exists():
                initial[preference['name']]=preference['values'].index(this_pref[0].preference_value)
            else:
                initial[preference['name']]=preference['values'].index(preference['default'])

        form = PreferenceForm(PREFERENCES,initial=initial)
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'member_profiles',
        'back_button':{'link':reverse('member_resources:profile',args=[request.user.username]),'text':'To Your Profile'},
        'submit_name':'Update Preferences',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'form_title':'Update Your Account Preferences',
        'help_text':'These preferences affect how your interactions with the website, your calendar integration and others.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def view_background_forms(request):
    if not Permissions.can_view_background_forms(request.user):
        request.session['error_message']='You are not authorized to view educational background forms.'
        return redirect('member_resources:index')
    background_forms = EducationalBackgroundForm.objects.all().order_by('id')
    template = loader.get_template('member_resources/view_background_forms.html')
    context_dict = {
        'forms':background_forms,
        'subnav':'misc_reqs',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def member_playground(request):
    if not hasattr(request.user, 'userprofile'): 
        request.session['error_message']='You must create a profile to access TBPlayground.'
        return redirect('member_resources:index')
    profile = request.user.userprofile
    links=[]
    links.append({'name':'Submit Affirmation','link':reverse('member_resources:submit_praise')})
    if profile.is_member:
        pass
    template = loader.get_template('member_resources/playground.html')
    context_dict = {
        'subnav':'playground',
        'links':links,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
    
def approve_praise(request,praise_id): 
    if not hasattr(request.user,'userprofile'):
        request.session['error_message']='You must create a profile to approve an affirmation.'
        return redirect('member_resources:index')
    tbp=get_object_or_404(TBPraise,id=praise_id)
    if not tbp.public:
        request.session['error_message']='You can only approve public affirmations.'
        return redirect('member_resources:member_playground')
    if not request.user.userprofile ==tbp.recipient:
        request.session['error_message']='You can only approve affirmations you received.'
        return redirect('member_resources:member_playground')
    tbp.approved=True
    tbp.save()
    request.session['success_message']='Affirmation successfully approved for posting'
    return redirect('member_resources:member_playground')
        
def submit_praise(request):
    if not hasattr(request.user,'userprofile'):
        request.session['error_message']='You must create a profile to send an affirmation.'
        return redirect('member_resources:index')
    PraiseForm = modelform_factory(TBPraise,exclude=('giver','date_added','approved',))
    PraiseForm.base_fields['recipient'].queryset=UserProfile.objects.all().order_by('last_name')
    if request.method == 'POST':

        form = PraiseForm(request.POST)
        if form.is_valid():
            instance=form.save(commit=False)
            instance.giver=request.user.userprofile
            instance.save()
            instance.email_praise()
            request.session['success_message']='Affirmation submitted successfully'
            return redirect('member_resources:member_playground')
        else:
            request.session['error_message']=INVALID_FORM_MESSAGE
    else:
        form = PraiseForm()
    template = loader.get_template('generic_form.html')
    context_dict = {
        'form':form,
        'subnav':'playground',
        'has_files':False,
        'base':'member_resources/base_member_resources.html',
        'submit_name':'Submit Praise/Affirmation',
        'back_button':{'link':reverse('member_resources:member_playground'),'text':'To Member Playground'},
        'form_title':'Affirm/Praise/Congratulate a member',
        'help_text':'Use this form to give some positive feedback to another member (or user). This can be done anonymously or attributed to you. You can also indicate that the feedback should be private to the recipient or public (other members/users can see it). This is only for *positive* feedback and should not be used as a means to provide anonymous criticism.',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def non_event_project(request,ne_id):
    n = get_object_or_404(NonEventProject,id=ne_id)
    #enforce permissions here!
    return non_event_project_meta_data(request,n)

def new_non_event_project(request):
    if not Permissions.can_create_events(request.user):
        request.session['error_message']='You are not authorized to create project reports.'
        return get_previous_page(request,alternate='event_cal:index')
    return non_event_project_meta_data(request,None)

def non_event_project_meta_data(request,ne_report):
    if ne_report:
        NonEventProjectForm = modelform_factory(NonEventProject, exclude=('term','project_report'))
    else:
        NonEventProjectForm = modelform_factory(NonEventProject, exclude=('project_report',))
        ne_report = None

    NonEventProjectForm.base_fields['leaders'].queryset=get_members().order_by('last_name')
    if request.method =='POST':
        if ne_report:
            form = NonEventProjectForm(request.POST,instance=ne_report)
        else:
            form = NonEventProjectForm(request.POST)
        
        if form.is_valid():
            nep = form.save()
            request.session['success_message']='Non-event project created successfully'
            return redirect('member_resources:non_event_project_participants',nep.id)
        else:
            request.session['error_message']='Form contained errors, was not saved.'
    else:
        if ne_report:
            form = NonEventProjectForm(instance=ne_report)
        else:
            form = NonEventProjectForm()
    template = loader.get_template('generic_form.html')
    dp_ids=['id_start_date','id_end_date']
    context_dict ={
        'form':form,
        'dp_ids':dp_ids,
        'subnav':'history',
        'has_files':False,
        'submit_name':'Create/update non-event project',
        'form_title':'Create non-event project',
        'help_text':'These are for reports sent to the national organization to determine eligibility for certain chapter awards. They are also used for transition material to help future project leaders perform a similar event. Please be descriptive in your responses. Note that this form contains the meta-data for the project, you\'ll be asked to submit 2 additional forms with it.',
        'base':'member_resources/base_member_resources.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))

def non_event_project_participants(request,ne_id):
    ne = get_object_or_404(NonEventProject,id=ne_id)
    NonEventFormSet = modelformset_factory(NonEventProjectParticipant,exclude=('project',))
    NonEventFormSet.form.base_fields['participant'].queryset=get_members().order_by('last_name')

    if request.method =='POST':
        formset = NonEventFormSet(request.POST,queryset=NonEventProjectParticipant.objects.filter(project=ne).order_by('participant__last_name'),prefix='nep_parts')
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.project = ne
                instance.save()
            request.session['success_message']='Non-event project participants updated successfully'
            return redirect('event_cal:non_event_project_report',ne_id)
        else:
            request.session['error_message']='Form contained errors, was not saved.'
    else:
        formset = NonEventFormSet(queryset=NonEventProjectParticipant.objects.filter(project=ne).order_by('participant__last_name'),prefix='nep_parts')
    template = loader.get_template('generic_formset.html')
    context_dict ={
        'formset':formset,
        'can_add_row':True,
        'subnav':'history',
        'has_files':False,
        'prefix':'nep_parts',
        'submit_name':'Update non-event project participants',
        'form_title':'Update non-event project participants',
        'help_text':'These are for reports sent to the national organization to determine eligibility for certain chapter awards. They are also used for transition material to help future project leaders perform a similar event. Please be descriptive in your responses. Note that this form contains the participants for the project, you\'ll be asked to submit 1 additional form with it.',
        'base':'member_resources/base_member_resources.html',
        }
    context_dict.update(get_permissions(request.user))
    context_dict.update(get_common_context(request))
    context = RequestContext(request,context_dict )
    return HttpResponse(template.render(context))
