import json
import os
import subprocess
from datetime import date
from decimal import Decimal
from numpy import std,median,mean
import tweepy

from django.core.files import File
from django.db import models
from django.core.validators import  MinValueValidator
from localflavor.us.models import PhoneNumberField
from stdimage import StdImageField

from event_cal.models import EventShift,EventPhoto
from mig_main.models import MemberProfile,UserProfile,OfficerPosition,AcademicTerm
from mig_main.pdf_field import ContentTypeRestrictedFileField,pdf_types
from migweb.settings import  twitter_token,twitter_secret
from requirements.models import ProgressItem

# Create your models here.
class Officer(models.Model):
    user            = models.ForeignKey('mig_main.MemberProfile',
                                        on_delete=models.PROTECT)   
    term            = models.ManyToManyField('mig_main.AcademicTerm')
    position        = models.ForeignKey('mig_main.OfficerPosition',
                                        on_delete=models.PROTECT)
    website_bio     = models.TextField()
    website_photo   = StdImageField(upload_to='officer_photos',variations={'thumbnail':(555,775)})
    @classmethod
    def get_current_members(cls):
        current_officers = cls.objects.filter(term=AcademicTerm.get_current_term())
        return MemberProfile.objects.filter(officer__in = current_officers).distinct().order_by('last_name','first_name','uniqname')
    def __unicode__(self):
        return self.user.get_full_name()+': '+self.position.name

class Distinction(models.Model):
    member          = models.ForeignKey('mig_main.MemberProfile')
    term            = models.ForeignKey('mig_main.AcademicTerm')
    distinction_type= models.ForeignKey('requirements.DistinctionType')
    gift            = models.CharField(max_length=128)

    @classmethod
    def add_statuses(cls,uniqnames,distinction_type,term=None,gift='N/A'):
        if not term:
            term = AcademicTerm.get_current_term()
        no_profiles=[]
        for uniqname in uniqnames:
            profiles = MemberProfile.objects.filter(uniqname=uniqname)
            if not profiles.exists():
                no_profiles.append(uniqname)
                continue
            dist = cls(member=profiles[0],term=term,gift=gift,distinction_type=distinction_type)
            dist.save()
        return no_profiles
    def __unicode__(self):
        return unicode(self.term)+' '+unicode(self.distinction_type)+' for '+unicode(self.member)
        
class WebsiteArticle(models.Model):
    created_by      = models.ForeignKey('mig_main.MemberProfile',
                                        on_delete = models.SET_NULL,
                                        null=True,related_name='article_created_by')
    title           = models.CharField(max_length=250)
    body            = models.TextField()
    date_posted     = models.DateField()
    tagged_members  = models.ManyToManyField('mig_main.MemberProfile', blank=True,
                                            null=True,related_name='article_tagged_members')
                                            
    approved = models.BooleanField(default=False)
    
    @classmethod
    def get_stories(cls):
        return cls.objects.order_by('-date_posted').exclude(date_posted__gt=date.today()).exclude(approved=False)
    def __unicode__(self):
        return self.title+' ('+str(self.date_posted)+')'

    def get_short_view(self):
        if '<fold>' in self.body:
            fold_index = self.body.find('<fold>')
            return self.body[:fold_index]+'*Click title for full article*'
        return self.body
    def get_full_view(self):
        return self.body.replace('<fold>','')
        
    def tweet_story(self,include_hashtag):
        f = open('/srv/www/twitter.dat','r')
        token = json.load(f)
        f.close()
        auth = tweepy.OAuthHandler(twitter_token,twitter_secret)
        auth.set_access_token(token[0],token[1])
        api = tweepy.API(auth)
        if include_hashtag:
            hashtag='\n#UmichEngin'
        else:
            hashtag=''
        max_name_length = 140-25-len(hashtag)-15
        name=self.name
        if len(name)>max_name_length:
            name = name[:(max_name_length-3)]+'...'
        tweet_text = "%(name)s:\nRead more at:\n%(link)s%(hashtag)s"%{'name':name,'link':'https://tbp.engin.umich.edu'+reverse('history:get_article_view',args=(self.id,)),'hashtag':hashtag }
        
        api.update_status(tweet_text)
class Publication(models.Model):
    date_published  = models.DateField()
    volume_number   = models.PositiveSmallIntegerField()
    edition_number  = models.PositiveSmallIntegerField()
    name            = models.CharField(max_length=70)
    PUBlICATION_TYPES=[
                    ('CS','Cornerstone'),
                    ('AN','Alumni News')
                ]
    type            = models.CharField(max_length=2,
                                        choices=PUBlICATION_TYPES,
                                        default='CS')
    pdf_file        = ContentTypeRestrictedFileField(
        upload_to='newsletters',
        content_types=pdf_types,
        max_upload_size=104857600,
    )
    def __unicode__(self):
        return self.name
class MeetingMinutes(models.Model):
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='minutes',
            content_types=pdf_types,
            max_upload_size=104857600,
    )
    MEETING_TYPES=[
            ('NI','New Initiatives'),
            ('MM','Main Meetings'),
            ('OF','Officer Meetings'),
            ('AD','Advisory Board Meetings'),
        ]
    meeting_type = models.CharField(max_length=2,
            choices=MEETING_TYPES,
            default='MM')
    semester = models.ForeignKey('mig_main.AcademicTerm')
    meeting_name = models.CharField(max_length=80)
    def __unicode__(self):
        return self.meeting_name+' minutes.'

class GoverningDocumentType(models.Model):
    name = models.CharField(max_length=40)
    def __unicode__(self):
        return self.name

class GoverningDocument(models.Model):
    document_type = models.ForeignKey(GoverningDocumentType)
    active = models.BooleanField(default=True)
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='governing_docs',
            content_types=pdf_types,
            max_upload_size=104857600,
    )
    def __unicode__(self):
        if self.active:
            return 'Current '+unicode(self.document_type)
        else:
            return 'Old '+unicode(self.document_type)
class AwardType(models.Model):
    name = models.CharField(max_length=256)
    def __unicode__(self):
        return self.name

class Award(models.Model):
    award_type = models.ForeignKey(AwardType)
    term = models.ForeignKey('mig_main.AcademicTerm')
    recipient = models.ForeignKey('mig_main.MemberProfile')
    comment = models.TextField(blank=True)
    def __unicode__(self):
        return unicode(self.award_type)+' for '+unicode(self.term)+': '+unicode(self.recipient)
class CompiledProjectReport(models.Model):
    term = models.ForeignKey('mig_main.AcademicTerm')
    is_full = models.BooleanField(default=False)
    associated_officer = models.ForeignKey('mig_main.OfficerPosition')
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='compiled_project_reports',
            content_types=pdf_types,
            max_upload_size=214958080,
    )
    def __unicode__(self):
        if self.is_full:
            return 'Full Project Report for '+unicode(self.term.year)
        else:
            return unicode(self.term)+' Project Reports for '+unicode(self.associated_officer)

class NonEventProject(models.Model):
    name            = models.CharField(max_length=50)
    description     = models.TextField()
    leaders         = models.ManyToManyField('mig_main.MemberProfile',
                                             related_name ="non_event_project_leader")
    assoc_officer   = models.ForeignKey('mig_main.OfficerPosition')
    project_report  = models.ForeignKey('history.ProjectReport',null=True,blank=True,
                                        on_delete = models.SET_NULL)
    term            = models.ForeignKey('mig_main.AcademicTerm', default=AcademicTerm.get_current_term)    
    start_date      = models.DateField()
    end_date        = models.DateField()
    location        = models.CharField(max_length=100,blank=True,null=True)
    def __unicode__(self):
        return self.name

class NonEventProjectParticipant(models.Model):
    project = models.ForeignKey(NonEventProject)
    participant       = models.ForeignKey('mig_main.UserProfile')
    hours    = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0)])

class NonEventParticipantAlt(models.Model):
    project = models.ForeignKey(NonEventProject)
    participant_name = models.CharField(max_length=128)
    participant_status = models.ForeignKey('mig_main.Status')
    hours    = models.DecimalField(max_digits=5,decimal_places=2,validators=[MinValueValidator(0)])


class ProjectReport(models.Model):
    name = models.CharField(max_length=128, verbose_name='Project Name')
    term        = models.ForeignKey('mig_main.AcademicTerm')
    relation_to_TBP_objectives=models.TextField()
    
    is_new_event    = models.BooleanField(default=False)
    
    organizing_hours= models.PositiveSmallIntegerField()
    planning_start_date = models.DateField()
    TARGET_AUDIENCE_CHOICES = [
                        ('COMM','Community'),
                        ('UNIV','University'),
                        ('PROF','Profession'),
                        ('CHAP','Chapter'),
                        ('HON','Honors/Awards')
                    ]
    target_audience         = models.CharField(max_length=4,
                                                choices=TARGET_AUDIENCE_CHOICES,
                                                default='COMM')
    

    #Contact info: 
    contact_name            = models.CharField(max_length=75,
                                                blank=True)
    contact_email           = models.EmailField(max_length=254,
                                                blank=True)
    contact_phone_number    = PhoneNumberField(blank=True)
    contact_title           = models.CharField(max_length=75,
                                                blank=True)
    other_info              = models.CharField(max_length=150,
                                                blank=True)
    other_group             = models.CharField(max_length=60,
                                                blank=True)
    
    general_comments        = models.TextField()
    
    items                   = models.TextField()
    
    cost                    = models.PositiveIntegerField()
    
    problems_encountered    = models.TextField()
    
    recommendations         = models.TextField()
    evaluations_and_results = models.TextField()
    
    one_to_five =[('1','1:Best'),('2','2'),('3','3'),('4','4'),('5','5: Worst')]
    rating                  = models.CharField(max_length=1,
                                                choices=one_to_five,
                                                default='3')
    best_part               = models.TextField()
    opportunity_to_improve  = models.TextField()
    recommend_continuing    = models.BooleanField()

    def __unicode__(self):
        return self.name
    def get_descriptions(self):
        has_events = self.calendarevent_set.count()>0
        if has_events:
            events = self.calendarevent_set.all()
            description ='\n'.join(list(set([e.description for e in events])))
        else:
            neps = self.noneventproject_set.all()
            description = '\n'.join(list(set([n.description for n in neps])))
        return description

    def set_description(self,description):
        has_events = self.calendarevent_set.count()>0
        if has_events:
            events = self.calendarevent_set.all()
            for event in events:
                event.description=description
                event.save()
        else:
            neps = self.noneventproject_set.all()
            for nep in neps:
                nep.description = description
                nep.save()

    def get_associated_officer(self):
        has_events = self.calendarevent_set.count()>0
        if has_events:
            return self.calendarevent_set.all()[0].assoc_officer
        else:
            return self.noneventproject_set.all()[0].assoc_officer
    def write_tex_file(self):
        f = open('/tmp/project_report%d.tex'%(self.id),'w')
        f.write(self.print_to_tex().encode('utf8'))
        f.close()
    def fix_quotes(self,string):
        blocks = string.split('\"')
        out_string = blocks[0]
        token = '``'
        for block in blocks[1:]:
            out_string+=token
            out_string+=block
            if token =='``':
                token = '\"'
            else:
                token = '``'
        return out_string
    def is_url(self,word):
        if word.startswith('http'):
            return True
        if word.startswith('www.'):
            return True
        if word.count('@')>0:
            return False
        if word.endswith('.com') or word.endswith('.edu') or word.endswith('.org'):
            return True
        if word.endswith('.gov') or word.endswith('.html') or word.endswith('.cfm'):
            return True
        if word.endswith('.htm') or word.endswith('.ca') or word.endswith('.net'):
            return True
        return False
    def clean_tex_string(self,input_string):
        output = input_string.replace(r'%',r'''\%''')
        output = output.replace('$','\\$')
        output = output.replace('&','\\&')
        output = output.replace('_','\\_')
        output=output.replace(r'#',r'\#')
        output=self.fix_quotes(output)
        words = output.split()
        count = 0
        while count<len(words):
            word = words[count]
            if self.is_url(word):
                words[count]=r'''\url{'''+word+r'''}'''
            count+=1
        return ' '.join(words)
    def print_to_tex(self):
        has_events = self.calendarevent_set.count()>0
        if has_events:
            events = self.calendarevent_set.all()
            duration = sum([event.get_max_duration().total_seconds()/3600. for event in events])
            if events.count()>1:
                hours_string = '(Total Duration for %d Events)'%(events.count())
            else:
                hours_string = '(Event Duration)'
            leaders = MemberProfile.objects.filter(event_leader__in=events).distinct()
            shifts = EventShift.objects.filter(event__in=events).distinct()
            desc = list(set([e.description for e in events]))
            desc_string ='\n'.join(desc)
            all_dates = []
            for shift in shifts:
                all_dates.append(shift.start_time.date())
                all_dates.append(shift.end_time.date())
            all_dates = sorted(list(set(all_dates)))
            date_string = ', '.join([date.strftime('%x') for date in all_dates])
            if len(all_dates)>1:
                date_string = 's: '+date_string
            else:
                date_string = ': '+date_string
            progress_items = ProgressItem.objects.filter(related_event__in = events).order_by('member').distinct()
            attendees={}
            active_count = 0
            electee_count = 0
            non_member_count = 0
            for item in progress_items:
                if item.related_event.is_fixed_progress():
                    scale = Decimal(item.related_event.get_max_duration().total_seconds()/3600.)
                else:
                    scale = Decimal(1.0)
                if item.member in attendees.keys():
                    attendees[item.member]+=scale*item.amount_completed
                else:
                    attendees[item.member]=scale*item.amount_completed
                    if not item.member.init_term == self.term:
                        active_count +=1
                    else:
                        electee_count+=1
            all_attendees=UserProfile.objects.filter(event_attendee__event__in=events).distinct()
            non_members = [member for member in all_attendees if not member.is_member()]
            non_member_count = len(non_members)
            leader_string = r'''Project Leader(%s) (uniqname)\\
            \begin{tabular}{|l|}\hline
            '''%('s' if leaders.count>1 else '')
            for leader in leaders:
                if leader not in attendees:
                    if not leader.init_term == self.term:
                        active_count +=1
                    else:
                        electee_count +=1
                leader_string +=r'''%s (%s)\\ 
                '''%(leader.get_firstlast_name(),leader.uniqname)
            leader_string+=r'''\hline 
            \end{tabular}\paraspace
            '''
            attendee_string = r'''\begin{longtable}{|lr|c|r|}\hline Name&(uniqname)&Active/Electee/Non-Member & Number of Hours\\ \hline
            \endhead
            \hline
            \endfoot
            '''
            profiles = MemberProfile.objects.filter(progressitem__in=progress_items).order_by('last_name','first_name').distinct()
            for member in profiles:
                attendee_string+=r'''%s&(%s)&%s&%.2f\\
                '''%(member.get_firstlast_name(),member.uniqname,'Active' if not member.init_term ==self.term else 'Electee',attendees[member])
            for non_member in non_members:
                hours = sum([ event.get_attendee_hours_at_event(non_member)  for event in events])
                attendee_string+=r'''%s& (%s) & Non-Member & %.2f\\
                '''%(non_member.get_firstlast_name(),non_member.uniqname,hours)        
            attendee_string +=r'\end{longtable}'
            num_part_string = r'''Active Members:~%d\hspace{.5in}Electees:~%d'''%(active_count,electee_count)
            duration_s='%d'%(duration)
        else:
            neps=self.noneventproject_set.all()
            if neps.count()<1:
                return 0
            if neps.count()>1:
                return -1
            nep=neps[0]
            date_string = 's: %s--%s '%(nep.start_date.strftime('%x'), nep.end_date.strftime('%x'))
            participants = nep.noneventprojectparticipant_set.all()
            participants2 = nep.noneventparticipantalt_set.all()
            leaders= nep.leaders.all()
            attendees={}
            active_count = 0
            electee_count = 0
            non_member_count=0
            for item in participants:
                if item.participant in attendees.keys():
                    attendees[item.participant]+=item.hours
                else:
                    attendees[item.participant]=item.hours
                    if not item.participant.is_member():
                        non_member_count+=1
                    elif not item.participant.memberprofile.init_term == self.term:
                        active_count +=1
                    else:
                        electee_count+=1
            for item in participants2:
                if item.participant_status.name=='Active':
                    active_count+=1
                elif item.participant_status.name=='Electee':
                    electee_count+=1
            leader_string = r'''Project Leader(%s) (uniqname)\\
            \begin{tabular}{|l|}\hline
            '''%('s' if leaders.count>1 else '')
            for leader in leaders:
                if UserProfile.objects.get(uniqname=leader.uniqname) not in attendees:
                    if not leader.init_term == self.term:
                        active_count +=1
                    else:
                        electee_count +=1
                leader_string +=r'''%s (%s)\\
                '''%(leader.get_firstlast_name(),leader.uniqname)
            leader_string+=r'''\hline
            \end{tabular}\paraspace
            '''
            attendee_string = r'''\begin{longtable}{|lr|c|r|}\hline Name&(uniqname)&Active/Electee/Non-Member & Number of Hours\\ \hline
            \endhead
            \hline
            \endfoot
            '''
            profiles = UserProfile.objects.filter(noneventprojectparticipant__in=participants).order_by('last_name','first_name')
            for member in profiles:
                if not member.is_member():
                    status_string = 'Non-member'
                elif not member.memberprofile.init_term==self.term:
                    status_string = 'Active'
                else:
                    status_string = 'Electee'
                attendee_string+=r'''%s&(%s)&%s&%.2f\\
                '''%(member.get_firstlast_name(),member.uniqname,status_string,attendees[member])
            for member in participants2:
                name_and_uniqname = member.participant_name.replace(')','').strip().split('(')
                attendee_string+=r'''%s &(%s)& %s & %.2f\\
                '''%(name_and_uniqname[0],name_and_uniqname[1],member.participant_status,member.hours)
            attendee_string +=r'\end{longtable}'
            num_part_string = r'Active Members:~%d\hspace{.5in}Electees:~%d'%(active_count,electee_count)
            desc_string = nep.description
            duration_s='N/A'
            hours = [float(attendees[member]) for member in profiles]
            hours+=[float(member.hours) for member in participants2]
            if std(hours)<.5:
                duration_s = '%.1f'%median(hours)
            if std(hours)<.2:
                hours_string=''
            else:
                hours_string = 'Varies by participant'

        if self.is_new_event:
            new_project = r'Yes'
        else:
            new_project = r'No'
        if self.contact_name or self.contact_email or self.contact_phone_number or self.contact_title or self.other_info:
            contact_string = r'''\item Contact Information\\
                    \begin{tabular}{l p{5in}}
                    '''
            if self.contact_name:
                contact_string+=r'''Name:    &   %s\\
                '''%(self.contact_name)
            if self.contact_title:
                contact_string+=r'''Title:    &   %s\\
                '''%(self.contact_title)
            if self.contact_email:
                contact_string+=r'''Email:    &   %s\\
                '''%(self.contact_email)
            if self.contact_phone_number:
                contact_string+=r'''Phone\#:    &   %s\\
                '''%(self.contact_phone_number)
            if self.other_info:
                contact_string+=r'''Other Info:    &   %s\\
                '''%(self.clean_tex_string(self.other_info))
            contact_string+=r'''\end{tabular}
            '''
        else:
            contact_string=''
        if self.other_group:
            other_group_string = r'''\item Other Organizations Participating: %s
            '''%(self.other_group)
        else:
            other_group_string=''
        project_photos = EventPhoto.objects.filter(project_report = self)
        if project_photos.exists():
            picture_string = r'''\item \textbf{Pictures:}
            '''
            for photo in project_photos.order_by('id'):
                picture_string+=r'''\begin{figure}[htb]
                \centering
                \includegraphics[max width = .9\textwidth]{%(picture_name)s}
                \caption{%(caption)s}
                \end{figure}
                '''%{'picture_name':photo.photo.name,'caption':self.fix_quotes(photo.caption)}
        else:
            picture_string=''

        output_string = r'''\section{%(project_name)s}
        \begin{enumerate}[I.]
            \item \textbf{Basic Information:}
            \begin{enumerate}[1.]
                \item Project Date%(dates)s (Planning started: %(planning_date)s)
                \item Project was new?: %(new_project)s
                \item Number of participants:\\
                        %(participant_numbers)s
                \item Names of participants:\\
                        %(participant_names)s
            \end{enumerate}
            \item \textbf{General Description:} %(description)s
            \item \textbf{Target Audience:} %(audience)s
            \item \textbf{Relationship to the Objectives of MI-G:} %(objectives)s
            \item \textbf{Organization and Administration}
            \begin{enumerate}[1.]
                %(contact_string)s
                \item Hours spent on the project:\\
                        Organizing: %(org_hours)d\hspace{.3in} Participating: %(part_hours)s %(hours_string)s
                %(other_group)s
            \end{enumerate}
            \item\textbf{Cost and Personnel Requirements}
            \begin{enumerate}[1.]
                \item General Comments: %(gen_comments)s
                \item Items Needed: %(items)s
                \item Total Cost: \$%(cost)s
            \end{enumerate}
            \item \textbf{Problems Encountered:} %(problems)s
            \item \textbf{Recommendations:} %(recommend)s
            \item \textbf{Overall Evaluation:}
            \begin{enumerate}[1.]
                \item Comments: %(eval_results)s
                \item Overall Rating (1 is best; 5 is worst): %(rating)s
                \item Best Part: %(best_part)s
                \item Opportunity to improve: %(improve)s
                \item Do you recommend continuing?: %(continue)s
            \end{enumerate}
            %(picture_string)s


        \end{enumerate}
        '''%{
            'project_name':self.name,
            'dates':date_string,
            'planning_date':self.planning_start_date.strftime('%x'),
            'new_project':new_project,
            'participant_numbers':num_part_string,
            'participant_names':leader_string+attendee_string,
            'description':self.clean_tex_string(desc_string),
            'audience':self.get_target_audience_display(),
            'objectives':self.clean_tex_string(self.relation_to_TBP_objectives),
            'contact_string':contact_string,
            'org_hours':self.organizing_hours,
            'part_hours':duration_s,
            'hours_string':hours_string,
            'other_group':other_group_string,
            'gen_comments':self.clean_tex_string(self.general_comments),
            'items':self.clean_tex_string(self.items),
            'cost':self.cost,
            'problems':self.problems_encountered,
            'recommend':self.clean_tex_string(self.recommendations),
            'eval_results':self.clean_tex_string(self.evaluations_and_results),
            'rating':self.rating,
            'best_part':self.clean_tex_string(self.best_part),
            'improve':self.clean_tex_string(self.opportunity_to_improve),
            'continue':('Yes' if self.recommend_continuing else 'No'),
            'picture_string':picture_string

        }
        return output_string

class ProjectReportHeader(models.Model):
    executive_summary = models.TextField()
    preparer = models.ForeignKey('mig_main.MemberProfile')
    preparer_title = models.CharField(max_length = 128)
    terms = models.ManyToManyField('mig_main.AcademicTerm')

    finished_processing=models.BooleanField(default=False)
    finished_photos=models.BooleanField(default=False)
    last_processed=models.PositiveIntegerField(default=0)
    last_photo=models.PositiveIntegerField(default=0)
    def get_project_reports(self):
        return ProjectReport.objects.filter(term__in = self.terms.all())

    def write_tex_files(self):
        f = open('/tmp/Project_Report_Final_%d.tex'%(self.id),'w')
        years = '--'.join([str(term.year) for term in self.terms.all().order_by('year').distinct()])
        print years
        print self.preparer_title
        output_string = r'''\documentclass{ProjectReport}
        \usepackage{placeins}
        \usepackage{fontspec}
        \setmainfont[Ligatures=TeX]{Linux Libertine O}
        \graphicspath{{/srv/www/migweb/media/}}
        \begin{document}
        \newpage
         \null

         \thispagestyle{empty}
          \begin{center}
            \quad\\[2 in]
              \bf \LARGE The Michigan Gamma Chapter of Tau~Beta~Pi\\ Presents: \\[3 in]
               \bf \huge Project Reports for the\\'''+years+r'''\\ Annual Chapter Survey
                \end{center}
                \newoddside
                \section*{}
                \thispagestyle{empty}'''+self.executive_summary+r'''\\
                Sincerely,\\
                        %\includegraphics[width=2in]{\@sigFile}\\
        '''+self.preparer.get_firstlast_name()+r'''
                        \\ MI-$\Gamma$'''+self.preparer_title+r'''~'''+years+r'''
                \newoddside
                        \begin{abstract}
                        This section lists all of the projects performed by the Michigan Gamma Chapter of Tau Beta Pi for the school year extending from September 2011 to May 2012. The projects presented here were categorized into five separate groups:
                        \begin{enumerate}[1.]
                        \item Professional: Projects which were performed to enhance the engineering skills and job opportunities for students as well as offer opportunities for students to interact with company representatives.
                        \item Community: Projects which were performed primarily as a service to the community and undertaken to enhance a spirit of liberal culture within the chapter.
                        \item University: Projects which were performed primarily as a service to the University and its students.
                        \item Chapter: Projects which were performed to aid to smooth operation of the chapter, stimulate the interaction between other chapters in the nation, or stimulate social interaction of our members within the college, with each other, and with other societies.
                        \item Honors: Projects which were performed to honor outstanding achievement within our chapter and the University.
                        \end{enumerate}
                        Each project occupies at least one sheet, the Chapter Project Summary. The summary was derived from the standard Project Report provided by the national organization. There is one summary sheet for each project; however, some projects were repeated in different weeks or semesters. For simplicity, some of the sections above were split into the fall and winter semester for the school year. Unfortunately, for some projects a complete list of
                        participants was not available due to the large number of members.
                        \end{abstract}
                        \newoddside
                        \tableofcontents
                        \newevenside
'''
        previous_category = 'None'
        officer_files = {}
        officer_sheet_header=r'''\documentclass{ProjectReport}
        \usepackage{placeins}
        \usepackage{fontspec}
        \setmainfont[Ligatures=TeX]{Linux Libertine O}
        \graphicspath{{/srv/www/migweb/media/}}
        \begin{document}
        \begin{titlepage}
        \begin{center}
        \textsc{\LARGE Tau Beta Pi Project Report Summary}\\[1.5cm]
        \textsc{\Large %(term)s}\\[.5cm]
        \rule{\linewidth}{0.5mm}\\[.4cm]
        {\huge\bfseries %(officer)s}\\[.4cm]
        \rule{\linewidth}{0.5mm}\\[1.5cm]
        This document contains the project reports related to your officer position. Please keep them as reference as and recommendation.\\
        \vfill
        {\large Last revised:}\\
        {\large \today}
        \end{center}
        \end{titlepage}

        '''
        for project in self.get_project_reports().order_by('target_audience','planning_start_date').distinct():
            if not previous_category == project.get_target_audience_display():
                previous_category = project.get_target_audience_display()
                output_string+=r'''\part{%s}
                '''%(previous_category)
            project.write_tex_file()
            if not project.get_associated_officer() in officer_files:
                officer_files[project.get_associated_officer()]={}
            if not project.term in officer_files[project.get_associated_officer()]:
                officer_files[project.get_associated_officer()][project.term]=open('/tmp/officer_proj_report_%s_%s.tex'%(project.get_associated_officer().id,project.term.id),'w')
                header_string =officer_sheet_header%{'officer':project.get_associated_officer().name,'term':unicode(project.term)}
                officer_files[project.get_associated_officer()][project.term].write(header_string.encode('utf8'))
            officer_files[project.get_associated_officer()][project.term].write((r'''\input{/tmp/project_report%d.tex}%% %s
            \FloatBarrier\newpage\clearpage'''%(project.id,project.name)).encode('utf8'))

            output_string+=r'''\input{/tmp/project_report%d.tex}%% %s
            \FloatBarrier\newpage\clearpage'''%(project.id,project.name)
        output_string+=r'''\end{document}'''
        cmd = 'xelatex -interaction=nonstopmode %(file_name)s'
        current_dir = os.getcwd()
        os.chdir('/tmp/')
        for officer in officer_files:
            for term in officer_files[officer]:
                officer_files[officer][term].write(r'''\end{document}'''.encode('utf8'))
                officer_files[officer][term].close()
                new_cmd =cmd%{'file_name':'/tmp/officer_proj_report_%d_%d.tex'%(officer.id,term.id)}
                print 'executing: '+new_cmd
                p = subprocess.Popen(new_cmd.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                p.communicate()
                if p.returncode==0:
                    p = subprocess.Popen(new_cmd.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    p.communicate()
                    print 'officer compilation successful'
                    if CompiledProjectReport.objects.filter(term=term,associated_officer=officer).exists():
                        c=CompiledProjectReport.objects.get(term=term,associated_officer=officer)
                    else:
                        c = CompiledProjectReport(term = term,associated_officer=officer,is_full=False)
                        c.save()
                    new_f = open('./officer_proj_report_%d_%d.pdf'%(officer.id,term.id),'r')
                    c.pdf_file.save('compiled_report_%d.pdf'%c.id,File(new_f),True)

        f.write(output_string.encode('utf8'))
        f.close()
        new_cmd = cmd%{'file_name':'/tmp/Project_Report_Final_%d.tex'%(self.id)}
        p = subprocess.Popen(new_cmd.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p.communicate()
        if p.returncode==0:
            p = subprocess.Popen(new_cmd.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p.communicate()
            print 'full compilation successful'
            if CompiledProjectReport.objects.filter(term=max(self.terms.all()),is_full=True).exists():
                c = CompiledProjectReport.objects.get(term=max(self.terms.all()),is_full=True)
            else:
                c = CompiledProjectReport(term=max(self.terms.all()),is_full=True,associated_officer=OfficerPosition.objects.get(name='Secretary'))
                c.save()
            new_f = open('./Project_Report_Final_%d.pdf'%(self.id),'r')
            c.pdf_file.save('compiled_report_%d.pdf'%c.id,File(new_f),True)
        os.chdir(current_dir)

class OfficerPositionRelationship(models.Model):
    predecessor = models.ForeignKey('mig_main.OfficerPosition',related_name='officer_relationship_predecessor')
    successor = models.ForeignKey('mig_main.OfficerPosition', related_name='officer_relationship_successor')
    effective_term = models.ForeignKey('mig_main.AcademicTerm')
    description = models.TextField()

    def __unicode__(self):
        return unicode(self.predecessor)+'->'+unicode(self.successor)+' in '+unicode(self.effective_term)
