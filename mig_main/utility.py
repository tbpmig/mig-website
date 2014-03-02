import csv,codecs,cStringIO

from django.db.models import Q
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


from electees.models import ElecteeGroup
from event_cal.models import CalendarEvent
from mig_main.models import AcademicTerm, OfficerPosition, MemberProfile,get_members,get_actives,get_electees
from requirements.models import SemesterType
from history.models import Officer,ProjectReport
from member_resources.models import ProjectLeaderList

from mig_main.default_values import get_current_term

def get_current_officers():
    current_officers = Officer.objects.filter(term=get_current_term())
    return MemberProfile.objects.filter(officer__in = current_officers).distinct()
def get_current_group_leaders():
    current_electee_groups = ElecteeGroup.objects.filter(term=get_current_term())
    return MemberProfile.objects.filter(electee_group_leaders__in = current_electee_groups).distinct()

def get_current_event_leaders():
    current_events = CalendarEvent.objects.filter(term=get_current_term())
    return MemberProfile.objects.filter(event_leader__in = current_events).distinct()


def get_message_dict(request):
    error_message=request.session.pop('error_message',None)
    warning_message=request.session.pop('warning_message',None)
    success_message=request.session.pop('success_message',None)
    info_message=request.session.pop('info_message',None)
    return {'error_message':error_message,
            'warning_message':warning_message,
            'success_message':success_message,
            'info_message':info_message,
            }

def get_next_term(term):
    new_type = None
    new_year = 0;
    if term.semester_type.name=='Fall':
        new_year=term.year+1
        new_type = SemesterType.objects.get(name='Winter')
    else:
        new_year = term.year
        if term.semester_type.name=='Winter':
            new_type = SemesterType.objects.get(name='Summer')
        else:
            new_type = SemesterType.objects.get(name='Fall')
    if AcademicTerm.objects.filter(year=new_year,semester_type=new_type).exists():
        return AcademicTerm.objects.get(year=new_year,semester_type=new_type)
    else:
        a = AcademicTerm(year=new_year,semester_type=new_type)
        a.save()
        return a

def get_next_full_term(term):
    new_type = None
    new_year = 0;
    if term.semester_type.name=='Fall':
        new_year=term.year+1
        new_type = SemesterType.objects.get(name='Winter')
    else:
        new_year = term.year
        new_type = SemesterType.objects.get(name='Fall')
    if AcademicTerm.objects.filter(year=new_year,semester_type=new_type).exists():
        return AcademicTerm.objects.get(year=new_year,semester_type=new_type)
    else:
        a = AcademicTerm(year=new_year,semester_type=new_type)
        a.save()
        return a

def get_previous_page(request,alternate='home',args=tuple()):
    if 'current_page' in request.session:
        return redirect(request.session['current_page'])
    else:
        if args:
            return redirect(alternate,*args)
        else:
            return redirect(alternate)

def get_quick_links(user):
    quick_links = []
    if not hasattr(user,'userprofile'):
        return quick_links
    if not user.userprofile.is_member():
        return quick_links
    profile = user.userprofile.memberprofile
    if profile.standing.name != 'Alumni':
        quick_links.append({'link':reverse('member_resources:view_progress',args=(profile.uniqname,)),'link_name':'Track My Progress'})
    positions = Permissions.get_current_officer_positions(user)
    if Permissions.can_add_announcements(user):
        quick_links.append({'link_name':'Add Weekly Announcement','link':reverse('event_cal:add_announcement')})
    if Permissions.can_view_more_than_own_progress(user):
        quick_links.append({'link_name':'View Members\' Progress','link':reverse('member_resources:view_progress_list')})
    # Pres items-nothing unique
    # VP items
    if positions.filter(Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')).exists():
        quick_links.append({'link_name':'Manage Requirements','link':reverse('member_resources:view_misc_reqs')})
        quick_links.append({'link_name':'Add Electees/Move to Actives','link':reverse('member_resources:manage_membership')})
        quick_links.append({'link_name':'Manage Electee Groups','link':reverse('electees:view_electee_groups')})
    # Secretary items - nothing unique
    # Treasurer items 
    if positions.filter(position__name='Treasurer').exists():
        quick_links.append({'link_name':'Manage Dues Payment','link':reverse('member_resources:manage_dues')})
    # Service Officer
    if positions.filter(position__name='Service Coordinator').exists():
        quick_links.append({'link_name':'Manage Project Leaders','link':reverse('member_resources:manage_project_leaders')})
    # K-12 Officer, Campus Outreach, Operations -nothing unique
    # Activities - nothing unique
    # Intersociety - nothing unique
    # NI, Corp, EVP, Historian - nothing unique
    # Publicity
    if positions.filter(position__name='Publicity Officer').exists():
        quick_links.append({'link_name':'Generate Weekly Announcements','link':reverse('event_cal:generate_announcements')})
    # Membership Officer -- also needs meeting sign-in once that's a thing
    if positions.filter(position__name='Membership Officer').exists():
        quick_links.append({'link_name':'Manage Requirements','link':reverse('member_resources:view_misc_reqs')})
        quick_links.append({'link_name':'Add/Manage Members','link':reverse('member_resources:manage_membership')})
        quick_links.append({'link_name':'View Meeting Surveys','link':reverse('member_resources:view_meeting_feedback')})
    #end officer permissions
    if Permissions.can_create_events(user):
        quick_links.append({'link_name':'Add new event to calendar','link':reverse('event_cal:create_event')}) 
    if Permissions.can_upload_minutes(user):
        quick_links.append({'link_name':'Upload Meeting Minutes','link':reverse('member_resources:upload_minutes')})  
    if Permissions.can_upload_articles(user):
        quick_links.append({'link_name':'Upload Article','link':reverse('history:upload_article')})
    if Permissions.can_post_web_article(user): 
        quick_links.append({'link':reverse('history:index'),'link_name':'Post Web Story'})
    return quick_links

class Permissions:
    @classmethod
    def get_profile(cls,user):
        if not hasattr(user,'userprofile'):
            return None 
        if not user.userprofile.is_member():
            return None
        return user.userprofile.memberprofile

    @classmethod
    def get_current_officer_positions(cls,user):
        profile = cls.get_profile(user)
        if not profile:
            return Officer.objects.none()
        term = get_current_term()
        if term.semester_type.name=='Summer':
            term = get_next_full_term()
        current_positions = Officer.objects.filter(user=profile,term = term)
        return current_positions
    
    @classmethod
    def can_create_events(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        profile = cls.get_profile(user)
        if not profile:
            return False
        if profile.projectleaderlist_set.all().exists():
            return True
        return False
    @classmethod
    def can_delete_events(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query = Q(position__name='President')|Q(position__name='Service Coordinator')|Q(position__name='New Initiatives Officer')|Q(position__name='Vice President')|Q(position__name='Activities Officer')
        if current_positions.filter(query).exists():
            return True
        else:
            return False
    @classmethod
    def can_update_mindset_materials(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Service Coordinator')|Q(position__name='K-12 Outreach Officer')|Q(position__name='Advisor')
        if current_positions.filter(query).exists():
            return True
        else:
            return False
    @classmethod
    def view_officer_meetings_by_default(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False

    @classmethod
    def can_access_history(cls, user):
        return cls.can_view_meeting_feedback(user) or cls.can_access_project_reports(user)

    @classmethod
    def can_access_project_reports(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        profile = cls.get_profile(user)
        if not profile:
            return False
        if profile.projectleaderlist_set.all().exists():
            return True
        return False
    @classmethod
    def can_view_meeting_feedback(cls, user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False
    @classmethod
    def can_add_external_service(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='Graduate Student Coordinator')|Q(position__name='Service Coordinator')|Q(position__name='Vice President')
        if current_positions.filter(query).exists():
            return True
        else:
            return False
    @classmethod
    def can_upload_articles(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Historian')|Q(position__name='New Initiatives Officer')
        if current_positions.filter(query).exists():
            return True
        else:
            return False
    @classmethod
    def can_add_announcements(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        return current_positions.all().exists()

    @classmethod
    def can_generate_announcements(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        #query = Q(position__name='President')|Q(position__name='Publicity Officer')|Q(position__name='New Initiatives Officer')
        if current_positions.exists():
            return True
        else:
            return False

    @classmethod
    def can_upload_minutes(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Secretary')|Q(position__name='New Initiatives Officer')
        if current_positions.filter(query).exists():
            return True
        else:
            return False
    @classmethod
    def can_post_web_article(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Historian')|Q(position__name='New Initiatives Officer')|Q(position__name='Publicity Officer')|Q(position__name='Website Officer')|Q(position__name='Advisor')
        if current_positions.filter(query).exists():
            return True
        else:
            return False

    @classmethod
    def can_view_others_progress(cls,user,uniqname2):
        if user.username == uniqname2:
            return True
        profile2 = MemberProfile.objects.filter(uniqname=uniqname2)
        if not profile2.exists():
            return False
        if user.is_superuser:
            return True
        if not hasattr(user,'userprofile'):
            return False
        if not user.userprofile.is_member():
            return False
        current_positions = cls.get_current_officer_positions(user) 
        if profile2[0].status.name=='Electee':
            query = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')
            if current_positions.filter(query).exists():
                return True
            elif ElecteeGroup.objects.filter(members=profile2[0],leaders=user.userprofile.memberprofile).exists():
                return True
            elif ElecteeGroup.objects.filter(members=profile2,officers=user.userprofile.memberprofile).exists():
                return True
            else:
                return False
        else:
            query = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Membership Officer')    
            if current_positions.filter(query).exists():
                return True
            else:
                return False
    @classmethod
    def can_view_more_than_own_progress(cls,user):
        if user.is_superuser:
            return True
        if not hasattr(user,'userprofile') or not user.userprofile.is_member():
            return False
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')|Q(position__name='Membership Officer')
        query2 = Q(leaders=user.userprofile.memberprofile)|Q(officers=user.userprofile.memberprofile)
        if current_positions.filter(query).exists():
            return True
        elif ElecteeGroup.objects.filter(query2).exists():
                return True
        else:
            return False
    @classmethod
    def project_reports_you_can_view(cls,user):
        if user.is_superuser:
            return ProjectReport.objects.filter(term=get_current_term())
        current_positions=cls.get_current_officer_positions(user)
        if current_positions.filter(position__name='Secretary').exists():
            return ProjectReport.objects.filter(term=get_current_term())
        profile =cls.get_profile(user)
        if not profile:
            return ProjectReport.objects.none()
        query = Q()
        events=CalendarEvent.objects.filter(term=get_current_term()).filter(~Q(project_report=None))
        for position in current_positions:
            query = query|Q(assoc_officer=position.position)
        query=query|Q(leaders=profile)
        events =events.filter(query)
        project_reports=[]
        for event in events:
            if not event.project_report in project_reports:
                project_reports.append(event.project_report)
        return project_reports
    @classmethod
    def profiles_you_can_view(cls,user):
        if user.is_superuser:
            return get_members()
        current_positions = cls.get_current_officer_positions(user) 
        query_all = Q(position__name='President')|Q(position__name='Vice President')
        query_actives = Q(position__name='Membership Officer')
        query_electees= Q(position__name='Graduate Student Coordinator')
        query_electee_groups = Q(leaders=user.userprofile.memberprofile)|Q(officers=user.userprofile.memberprofile)
        query_out = MemberProfile.objects.none()
        if current_positions:
            if current_positions.filter(query_all).exists():
                return get_members()
            if current_positions.filter(query_actives).exists():
                query_out = query_out | get_actives()
            if current_positions.filter(query_electees).exists():
                query_out = query_out | get_electees()
        
        electee_groups_led = ElecteeGroup.objects.filter(query_electee_groups)
        for electee_group in electee_groups_led:
            query_out = query_out|electee_group.members.all()

        return query_out
    
    @classmethod
    def can_add_leadership_credit(cls,user):
        if user.is_superuser:
            return True
        if cls.can_manage_active_progress(user):
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_other_people = Q(position__name='Service Coordinator')
        if current_positions.filter(query_other_people).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_active_progress(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_actives = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Membership Officer')
        if current_positions.filter(query_actives).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_electee_progress(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_electees = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')
        if current_positions.filter(query_electees).exists():
            return True
        else:
            return False
    @classmethod
    def can_add_electee_members(cls,user):
        if cls.can_manage_electee_progress(user):
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_add_electees = Q(position__name='Secretary')
        if current_positions.filter(query_add_electees).exists():
            return True
        return False
    @classmethod
    def can_change_grad_electee_requirements(cls,user):
        return cls.can_manage_electee_progress(user)

    @classmethod
    def can_change_ugrad_electee_requirements(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_positions = Q(position__name='President')|Q(position__name='Vice President')
        if current_positions.filter(query_positions).exists():
            return True
        else:
            return False
    @classmethod
    def can_change_active_requirements(cls,user):
        return cls.can_manage_active_progress(user)

    @classmethod
    def can_change_requirements(cls,user):
        return cls.can_change_active_requirements(user) or cls.can_change_ugrad_electee_requirements(user) or cls.can_change_grad_electee_requirements(user)

    @classmethod 
    def can_manage_misc_reqs(cls,user):
        return cls.can_manage_finances(user) or cls.can_manage_ugrad_paperwork(user)or cls.can_manage_grad_paperwork(user) or cls.can_approve_tutoring(user) or cls.can_add_leadership_credit(user) or cls.can_view_background_forms(user)

    @classmethod
    def can_approve_tutoring(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = Q(position__name='President')|Q(position__name='Service Coordinator')|Q(position__name='Campus Outreach Officer')
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False

    @classmethod
    def can_manage_finances(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = Q(position__name='President')|Q(position__name='Treasurer')
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False
    @classmethod
    def can_manage_ugrad_paperwork(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = Q(position__name='President')|Q(position__name='Vice President')
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False
    @classmethod
    def can_manage_grad_paperwork(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_dues = Q(position__name='President')|Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')
        if current_positions.filter(query_dues).exists():
            return True
        else:
            return False
    @classmethod
    def can_view_background_forms(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_forms = Q(position__name='President')|Q(position__name='Secretary')|Q(position__name='Vice President')|Q(position__name='Graduate Student Coordinator')
        if current_positions.filter(query_forms).exists():
            return True
        else:
            return False
    @classmethod
    def can_manage_membership(cls,user):
        return cls.can_manage_project_leaders(user) or cls.can_add_electee_members(user) or cls.can_manage_active_progress(user) or cls.can_manage_officers(user)
    @classmethod
    def can_manage_project_leaders(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        if current_positions.exists():
            return True
        return False
    
    @classmethod
    def can_manage_officers(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user)
        query_officers = Q(position__name='President')|Q(position__name='Website Officer')
        if current_positions.filter(query_officers).exists():
            return True
        return False
    @classmethod
    def can_change_website_term(cls,user):
        return user.is_superuser

    @classmethod
    def can_manage_website(cls,user):
        return user.is_superuser
    
    @classmethod
    def can_edit_corporate_page(cls,user):
        if user.is_superuser:
            return True
        current_positions = cls.get_current_officer_positions(user) 
        query = Q(position__name='President')|Q(position__name='Corporate Relations Officer')|Q(position__name='External Vice President')
        if current_positions.filter(query).exists():
            return True
        else:
            return False


class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8-sig", **kwds):
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
