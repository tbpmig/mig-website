import json

from django.http import HttpResponse
from django.shortcuts import  get_object_or_404
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.forms.models import modelformset_factory,modelform_factory
from django.forms import CheckboxSelectMultiple

from electees.models import ElecteeGroup, ElecteeGroupEvent,ElecteeResource,EducationalBackgroundForm,BackgroundInstitution
from mig_main.models import MemberProfile, AcademicTerm,get_actives
from mig_main.utility import Permissions, get_previous_page, get_current_officers, get_message_dict
from mig_main.default_values import get_current_term
from member_resources.views import get_permissions as get_member_permissions
from history.models import Officer
from electees.forms import get_unassigned_electees,InstituteFormset

def user_is_member(user):
    if hasattr(user,'userprofile'):
        if user.userprofile.is_member():
            return True
    return False
def get_permissions(user):
    permission_dict = get_member_permissions(user)
    permission_dict.update({
        'can_create_groups':Permissions.can_manage_electee_progress(user),
        'can_edit_resources':Permissions.can_manage_electee_progress(user),
        })
    return permission_dict
def get_common_context(request):
    context_dict=get_message_dict(request)
    context_dict.update({
        'request':request,
        'subnav':'electees',
    })
    return context_dict
def view_electee_groups(request):
    e_groups = ElecteeGroup.objects.filter(term=get_current_term()).order_by('points')
    packets = ElecteeResource.objects.filter(term=get_current_term(),resource_type__is_packet=True).order_by('resource_type')
    resources = ElecteeResource.objects.filter(term=get_current_term(),resource_type__is_packet=False).order_by('resource_type')
    template = loader.get_template('electees/view_electee_groups.html')
    context_dict = {
        'groups':e_groups,
        'resources':resources,
        'packets':packets,
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def edit_electee_groups(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to edit electee groups'
        return redirect('electees:view_electee_groups')
    e_groups = ElecteeGroup.objects.filter(term=get_current_term())
    ElecteeGroupFormSet = modelformset_factory(ElecteeGroup,exclude=('term','members','points',),can_delete=True,widgets={'leaders':CheckboxSelectMultiple,'officers':CheckboxSelectMultiple})
    ElecteeGroupFormSet.form.base_fields['leaders'].queryset=get_actives().order_by('last_name','first_name')
    #ElecteeGroupFormSet.form.base_fields['leaders'].widget=CheckboxSelectMultiple
    ElecteeGroupFormSet.form.base_fields['officers'].queryset=get_current_officers().order_by('last_name','first_name')
    if request.method =='POST':
        formset = ElecteeGroupFormSet(request.POST,prefix='groups')
        if formset.is_valid():
            instances=formset.save(commit=False)
            for instance in instances:
                if not instance.id:
                    instance.term = get_current_term()
                    instance.points = 0
                instance.save()
            formset.save_m2m()
            request.session['success_message']='Electee groups successfully updated'
            return redirect('electees:view_electee_groups')
        else:
            request.session['error_message']='Form is invalid. Please correct the noted errors'
    else:
        formset = ElecteeGroupFormSet(queryset=e_groups,prefix='groups')
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'groups',
        'subsubnav':'groups',
        'has_files':False,
        'submit_name':'Update Electee Groups',
        'form_title':'Update/Add/Remove Electee Groups',
        'help_text':'Create the electee groups for this semester, and specify the leaders nd officers. You can also remove or edit here.',
        'can_add_row':True,
        'base':'electees/base_electees.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

@ensure_csrf_cookie
def edit_electee_group_membership(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to edit electee groups'
        return redirect('electees:view_electee_groups')
    if request.method =='POST':
        electee_groups_json=request.POST['electee_groups']
        electee_groups = json.loads(electee_groups_json)
        for group_id in electee_groups:
            members = electee_groups[group_id]
            group = ElecteeGroup.objects.get(id=group_id)
            group.members.clear()
            for member in members:
                group.members.add(MemberProfile.objects.get(uniqname=member))
        request.session['success_message']='Your changes have been saved'

    e_groups = ElecteeGroup.objects.filter(term=get_current_term())
    template = loader.get_template('electees/edit_electee_group_membership.html')
    context_dict = {
        'electee_groups':e_groups,
        'unassigned_electees':get_unassigned_electees(),
        'subsubnav':'members',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def edit_electee_group_points(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to edit electee group points.'
        return redirect('electees:view_electee_groups')
    GroupPointsFormSet = modelformset_factory(ElecteeGroupEvent,exclude=('related_event_id',),can_delete=True)
    term =get_current_term()
    if request.method =='POST':
        formset = GroupPointsFormSet(request.POST,prefix='group_points',queryset=ElecteeGroupEvent.objects.filter(related_event_id=None,electee_group__term=term))
        if formset.is_valid():
            formset.save()
            request.session['success_message']='Electee group points updated successfully'
            return redirect('electees:view_electee_groups')
        else:
            request.session['error_message']='Form is invalid. Please correct the noted errors.'
    else:
        formset = GroupPointsFormSet(prefix='group_points',queryset=ElecteeGroupEvent.objects.filter(related_event_id=None,electee_group__term=term))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'group_points',
        'subsubnav':'points',
        'has_files':False,
        'submit_name':'Update Electee Group Points',
        'form_title':'Update/Add Remove Electee Group Points',
        'help_text':'Track the electee group points. You should not note any points from threshold participation at service or social events here. Those are tabulated automatically.',
        'can_add_row':True,
        'base':'electees/base_electees.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))

def submit_background_form(request):
    if not user_is_member(request.user) or not (request.user.userprofile.memberprofile.standing.name=='Graduate'):
        request.session['error_message']='You are not authorized to submit an educational background form.'
        return redirect('electees:view_electee_groups')
    BackgroundForm = modelform_factory(EducationalBackgroundForm,exclude=('member',))
    if request.method == 'POST':
        form = BackgroundForm(request.POST,prefix='background')
        formset = InstituteFormset(request.POST,prefix='institute')
        if form.is_valid():
            background_form = form.save(commit=False)
            background_form.member=request.user.userprofile.memberprofile
            formset = InstituteFormset(request.POST,prefix='institute',instance=background_form)
            formset[0].empty_permitted=False
            if formset.is_valid():
                background_form.save()
                form.save_m2m()
                formset.save()
                request.session['success_message']='Background form successfully'
                return redirect('electees:view_electee_groups')
            else:
                request.session['error_message']='Either there were errors in your prior degrees or you forgot to include one.'
        else:
            request.session['error_message']='There were errors in the submitted form, please correct the errors noted below.'
    else:
        form = BackgroundForm(prefix='background')
        formset= InstituteFormset(prefix='institute',instance=BackgroundInstitution())
    template = loader.get_template('electees/submit_education_form.html')
    context_dict = {
        'form':form,
        'formset':formset,
        'prefix':'institute',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
def edit_electee_resources(request):
    if not Permissions.can_manage_electee_progress(request.user):
        request.session['error_message']='You are not authorized to edit electee resources.'
        return redirect('electees:view_electee_groups')
    ResourceFormSet = modelformset_factory(ElecteeResource,exclude=('term',),can_delete=True)
    term =get_current_term()
    if request.method =='POST':
        formset = ResourceFormSet(request.POST,request.FILES,prefix='resources',queryset=ElecteeResource.objects.filter(term=term))
        if formset.is_valid():
            instances=formset.save(commit=False)
            for instance in instances:
                instance.term=term
                instance.save()
            request.session['success_message']='Electee resources updated successfully'
            return redirect('electees:view_electee_groups')
        else:
            request.session['error_message']='Form is invalid. Please correct the noted errors.'
    else:
        formset = ResourceFormSet(prefix='resources',queryset=ElecteeResource.objects.filter(term=term))
    template = loader.get_template('generic_formset.html')
    context_dict = {
        'formset':formset,
        'prefix':'resources',
        'has_files':True,
        'submit_name':'Update Electee Resources',
        'form_title':'Update/Add/Remove Electee Resources for %s'%(unicode(term)),
        'help_text':'These are the full packets and their constituent parts. If you need a part that isn\'t listed here, contact the web chair.',
        'can_add_row':True,
        'base':'electees/base_electees.html',
        }
    context_dict.update(get_common_context(request))
    context_dict.update(get_permissions(request.user))
    context = RequestContext(request, context_dict)
    return HttpResponse(template.render(context))
