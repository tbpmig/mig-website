import json
import os
import sys
import subprocess
from datetime import date, timedelta
from decimal import Decimal
from numpy import std, median, mean
import tweepy

from django.core.files import File
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from localflavor.us.models import PhoneNumberField
from stdimage import StdImageField

from event_cal.models import EventShift, EventPhoto
from mig_main.models import MemberProfile, UserProfile, OfficerPosition
from mig_main.models import AcademicTerm, OfficerTeam
from mig_main.pdf_field import ContentTypeRestrictedFileField, pdf_types
from migweb.settings import DEBUG, twitter_token, twitter_secret
from requirements.models import ProgressItem


RAW_TEX_STRING = r'''
\section{%(project_name)s}
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
                Organizing: %(org_hours)d\hspace{.3in}
                Participating: %(part_hours)s %(hours_string)s
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
'''

# %\includegraphics[width=2in]{\@sigFile}\\
RAW_HEADER_STRING = r'''
\documentclass{/srv/www/migweb/static/tex/ProjectReport}
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
   \bf \huge Project Reports for the\\%(years)s\\ Annual Chapter Survey
\end{center}
\newoddside
\section*{}
\thispagestyle{empty}
%(exec_summary)s\\
Sincerely,\\
%(preparer_name)s\\
MI-$\Gamma$ %(preparer_title)s~%(years)s
\newoddside
\begin{abstract}
This section lists all of the projects performed by the
Michigan Gamma Chapter of Tau Beta Pi for the school year
extending from September 2011 to May 2012. The projects
presented here were categorized into five separate groups:
\begin{enumerate}[1.]
    \item Professional: Projects which were performed to enhance
    the engineering skills and job opportunities for students as
    well as offer opportunities for students to interact with
    company representatives.
    \item Community: Projects which were performed primarily as a
    service to the community and undertaken to enhance a spirit of
    liberal culture within the chapter.
    \item University: Projects which were performed primarily as a
    service to the University and its students.
    \item Chapter: Projects which were performed to aid to smooth
    operation of the chapter, stimulate the interaction between
    other chapters in the nation, or stimulate social interaction
    of our members within the college, with each other, and with
    other societies.
    \item Honors: Projects which were performed to honor
    outstanding achievement within our chapter and the University.
\end{enumerate}
Each project occupies at least one sheet, the Chapter Project
Summary. The summary was derived from the standard Project
Report provided by the national organization. There is one
summary sheet for each project; however, some projects were
repeated in different weeks or semesters. For simplicity, some
of the sections above were split into the fall and winter
semester for the school year. Unfortunately, for some projects
a complete list of participants was not available due to the
large number of members.
\end{abstract}
\newoddside
\tableofcontents
\newevenside
'''


def pack_officers_for_term(term):
    """
    Groups the officers into the appropriate teams for display on the
    about/leadership page. Ensures that the Executive Committee is shown at
    the top of the page, and that the Vice President, who prior to Fall 2014
    was a member of two teams, only showed up in one.
    """
    officer_set = Officer.objects.filter(term=term)
    term_advisors = officer_set.filter(position__name='Advisor')

    term_officers = []
    team_q = Q(start_term__lte=term) & (Q(end_term__gte=term) |
                                        Q(end_term=None))
    for team in OfficerTeam.objects.filter(team_q):
        disp_order = 1
        if team.name == 'Executive Committee':
            disp_order = 0
        query = Q(position__in=team.members.all())
        if team.name == 'Electee and Membership Team':
            query = query & ~Q(position=team.lead)
        officers = officer_set.filter(query).order_by(
                                                'position__display_order',
                                                'id'
        )
        team_data = {
            'order': disp_order,
            'name': team.name,
            'lead_name': team.lead.name,
            'officers': officers.values('id')
        }
        term_officers.append(team_data)
    return {'officers': term_officers, 'advisors': term_advisors}


def default_term():
    # fixes the serialization issue
    return AcademicTerm.get_current_term()


# Create your models here.
class Officer(models.Model):
    """ An individual officer in a given term(s).

    Used to show who the officers are and also to assign website
    permissions appropriately.
    """
    user = models.ForeignKey('mig_main.MemberProfile',
                             on_delete=models.PROTECT)
    term = models.ManyToManyField('mig_main.AcademicTerm')
    position = models.ForeignKey('mig_main.OfficerPosition',
                                 on_delete=models.PROTECT)
    website_bio = models.TextField()
    website_photo = StdImageField(
                        upload_to='officer_photos',
                        variations={'thumbnail': (555, 775)}
    )

    @classmethod
    def get_current_members(cls):
        current_officers = cls.objects.filter(
                                    term=AcademicTerm.get_current_term()
        )
        profiles = MemberProfile.objects.filter(officer__in=current_officers)
        return profiles.distinct().order_by('last_name',
                                            'first_name',
                                            'uniqname')

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.user.get_full_name()+': '+self.position.name


class CommitteeMember(models.Model):
    """ A member of a committee.

    Used mostly for logging and for permisions.
    """
    committee = models.ForeignKey('mig_main.Committee')
    term = models.ForeignKey('mig_main.AcademicTerm')
    member = models.ForeignKey('mig_main.MemberProfile')
    is_chair = models.BooleanField(default=False)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return (unicode(self.member) +
                (' chair' if self.is_chair else ' member') +
                ' of the ' + unicode(self.committee) +
                ' for '+unicode(self.term))


class Distinction(models.Model):
    """ A record of someone achieving some status (Active, DA, PA)

    This is used for record keeping to determine DA terms, quorum, etc.
    """
    member = models.ForeignKey('mig_main.MemberProfile')
    term = models.ForeignKey('mig_main.AcademicTerm')
    distinction_type = models.ForeignKey('requirements.DistinctionType')
    gift = models.CharField(max_length=128)

    @classmethod
    def add_statuses(cls, uniqnames, distinction_type, term=None, gift='N/A'):
        if not term:
            term = AcademicTerm.get_current_term()
        no_profiles = []
        for uniqname in uniqnames:
            profiles = MemberProfile.objects.filter(uniqname=uniqname)
            if not profiles.exists():
                no_profiles.append(uniqname)
                continue
            dist = cls(
                    member=profiles[0],
                    term=term,
                    gift=gift,
                    distinction_type=distinction_type,
            )
            dist.save()
        return no_profiles

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return (unicode(self.term) +
                ' ' + unicode(self.distinction_type) +
                ' for ' + unicode(self.member))


class WebsiteArticle(models.Model):
    """ An article on the front page of the website.
    """
    created_by = models.ForeignKey(
                            'mig_main.MemberProfile',
                            on_delete=models.SET_NULL,
                            null=True,
                            related_name='article_created_by',
    )
    title = models.CharField(max_length=250)
    body = models.TextField()
    date_posted = models.DateField()
    tagged_members = models.ManyToManyField(
                            'mig_main.MemberProfile',
                            blank=True,
                            null=True,
                            related_name='article_tagged_members',
    )
    approved = models.BooleanField(default=False)

    @classmethod
    def get_stories(cls):
        stories = cls.objects.order_by('-date_posted')
        posted_stories = stories.exclude(date_posted__gt=date.today())
        return posted_stories.exclude(approved=False)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.title+' ('+str(self.date_posted)+')'

    def get_short_view(self):
        if '<fold>' in self.body:
            fold_index = self.body.find('<fold>')
            return self.body[:fold_index] + '*Click title for full article*'
        return self.body

    def get_full_view(self):
        return self.body.replace('<fold>', '')

    def tweet_story(self, include_hashtag):
        if not self.approved or DEBUG:
            return None
        f = open('/srv/www/twitter.dat', 'r')
        token = json.load(f)
        f.close()
        auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
        auth.set_access_token(token[0], token[1])
        api = tweepy.API(auth)
        if include_hashtag:
            hashtag = '\n#UmichEngin'
        else:
            hashtag = ''
        max_name_length = 140 - 25 - len(hashtag) - 15
        name = self.title
        if len(name) > max_name_length:
            name = name[:(max_name_length-3)]+'...'
        tweet_text = '%(name)s:\nRead more at:\n%(link)s%(hashtag)s' % {
                        'name': name,
                        'link': 'https://tbp.engin.umich.edu' + reverse(
                                                'history:article_view',
                                                args=(self.id,)
                        ),
                        'hashtag': hashtag
        }

        api.update_status(tweet_text)


class Publication(models.Model):
    """ A print publication, Cornerstone or Alumni Newsletter.

    Each object represents an issue.
    """
    date_published = models.DateField()
    volume_number = models.PositiveSmallIntegerField()
    edition_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=70)
    PUBlICATION_TYPES = [
            ('CS', 'Cornerstone'),
            ('AN', 'Alumni News')
    ]
    type = models.CharField(max_length=2,
                            choices=PUBlICATION_TYPES,
                            default='CS')
    pdf_file = ContentTypeRestrictedFileField(
        upload_to='newsletters',
        content_types=pdf_types,
        max_upload_size=104857600,
    )

    @classmethod
    def get_published(cls, document_type):
        today = date.today()
        return cls.objects.filter(
                    type=document_type
            ).order_by('date_published').exclude(date_published__gt=today)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.name


class MeetingMinutes(models.Model):
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='minutes',
            content_types=pdf_types,
            max_upload_size=104857600,
    )
    MEETING_TYPES = [
            ('NI', 'New Initiatives'),
            ('MM', 'Main Meetings'),
            ('OF', 'Officer Meetings'),
            ('AD', 'Advisory Board Meetings'),
            ('CM', 'Committee Meeting Minutes'),
        ]
    meeting_type = models.CharField(
                        max_length=2,
                        choices=MEETING_TYPES,
                        default='MM'
    )
    semester = models.ForeignKey('mig_main.AcademicTerm')
    meeting_name = models.CharField(max_length=80)
    display_order = models.PositiveIntegerField()

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.meeting_name+' minutes for '+unicode(self.semester)

    @classmethod
    def get_next_meeting_minutes_display_order(cls):
        minutes = cls.objects.filter(
                            semester=AcademicTerm.get_current_term()
        )
        return minutes.count()


class GoverningDocumentType(models.Model):
    """
    Represents a type of governing document of the chapter (constitution,
    bylaws, etc.)
    """
    name = models.CharField(max_length=40)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.name


class GoverningDocument(models.Model):
    """
    Represents a revision of a governing document of the chapter (Constitution,
    Bylaws, etc.).
    """
    document_type = models.ForeignKey(GoverningDocumentType)
    active = models.BooleanField(default=True)
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='governing_docs',
            content_types=pdf_types,
            max_upload_size=104857600,
    )

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        if self.active:
            return 'Current ' + unicode(self.document_type)
        else:
            return 'Old ' + unicode(self.document_type)


class AwardType(models.Model):
    """
    Represents a type of award the chapter gives out.
    """
    name = models.CharField(max_length=256)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return self.name


class Award(models.Model):
    """
    Represents an award given out at by the chapter, typically at the
    end of semester banquet.
    """
    award_type = models.ForeignKey(AwardType)
    term = models.ForeignKey('mig_main.AcademicTerm')
    recipient = models.ForeignKey('mig_main.MemberProfile')
    comment = models.TextField(blank=True)

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        return (unicode(self.award_type) +
                ' for '+unicode(self.term) +
                ': '+unicode(self.recipient))


class CompiledProjectReport(models.Model):
    """
    A completed and compiled yearly (or semesterly) project report summary.

    This is a model that wraps a pdf file of the project report summary to
    append the useful metadata (term, etc.).
    """
    term = models.ForeignKey('mig_main.AcademicTerm')
    is_full = models.BooleanField(default=False)
    associated_officer = models.ForeignKey('mig_main.OfficerPosition')
    pdf_file = ContentTypeRestrictedFileField(
            upload_to='compiled_project_reports',
            content_types=pdf_types,
            max_upload_size=214958080,
    )

    def __unicode__(self):
        """Returns the unicode representation of the object"""
        if self.is_full:
            if self.term.semester_type.name == 'Winter':
                return ('Full Project Report for ' +
                        unicode(self.term.year))
            else:
                return ('Fall Semester Checkpoint Report for ' +
                        unicode(self.term.year))
        else:
            return (unicode(self.term) +
                    ' Project Reports for ' +
                    unicode(self.associated_officer))


class NonEventProject(models.Model):
    """
    Represents a project that was not an event.

    Examples would include working on the website, making the alumni
    newsletters, etc. These objects contain the information that would
    otherwise be contained in an event object that is nonetheless needed to
    generate a project report.
    """
    name = models.CharField(max_length=50)
    description = models.TextField()
    leaders = models.ManyToManyField('mig_main.MemberProfile',
                                     related_name="non_event_project_leader")
    assoc_officer = models.ForeignKey('mig_main.OfficerPosition')
    project_report = models.ForeignKey(
                            'history.ProjectReport',
                            null=True,
                            blank=True,
                            on_delete=models.SET_NULL
    )
    term = models.ForeignKey('mig_main.AcademicTerm',
                             default=default_term)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(
                        max_length=100,
                        blank=True,
                        null=True
    )

    def __unicode__(self):
        """Returns a unicode representation of the object (its name)"""
        return self.name


class NonEventProjectParticipant(models.Model):
    """
    A participant in a project that was not an event (NonEventProject).

    Associates a userprofile with the number of hours they contributed at a
    particular project.
    """
    project = models.ForeignKey(NonEventProject)
    participant = models.ForeignKey('mig_main.UserProfile')
    hours = models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        validators=[MinValueValidator(0)]
    )


class NonEventParticipantAlt(models.Model):
    """
    Obsolete. Do Not Use.

    This was used during the transition to the new website to accommodate the
    fact that half of the project reports were entered into a google form and
    not the website. It is no longer of any practical use except because it is
    needed to keep data in the database.
    """
    project = models.ForeignKey(NonEventProject)
    participant_name = models.CharField(max_length=128)
    participant_status = models.ForeignKey('mig_main.Status')
    hours = models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        validators=[MinValueValidator(0)]
    )


class Policy(models.Model):
    """Contains information on the policy items adopted by the chapter.

    These are individual items of policy that have been adopted by some
    part of the chapter authorized to do so. The binding language is that
    which is contained in the language attribute, and influenced by the
    meta-data options. There are additional meta-data points that clarify who
    the policy effects, what it is regarding, and if it is active, that allow
    for searching, filtering, etc.
    """
    ADOPTED_BY_CHOICES = [
        ('A', 'Advisory Board'),
        ('O', 'Officer Corps'),
        ('C', 'Chapter Membership'),
    ]
    CATEGORY_CHOICES = [
        ('M', 'Membership'),
        ('L', 'Leadership'),
        ('A', 'Activities'),
        ('I', 'Image'),
        ('F', 'Finance'),
    ]
    SCOPE_CHOICES = [
        ('AB', 'Advisory Board'),
        ('OC', 'Officer Corps'),
        ('OT', 'Individual Officer Team'),
        ('IO', 'Individual Officer'),
        ('AC', 'Active members'),
        ('EL', 'Electees and candidates'),
        ('M', 'All members'),
    ]
    # Attributes
    adopted_by = models.CharField(max_length=1,
                                  choices=ADOPTED_BY_CHOICES)
    adopted_date = models.DateField()
    category = models.CharField(max_length=1,
                                choices=CATEGORY_CHOICES)
    effective_until = models.DateField(null=True, blank=True)
    language = models.TextField()
    original_intent = models.TextField(blank=True, null=True)
    scope = models.CharField(max_length=2,
                             choices=SCOPE_CHOICES)

    # Methods


class ProjectReport(models.Model):
    """
    Contains the information that is necessary to generate a project's end of
    year report. Uses information from the associated CalendarEvent or
    NonEventProject object.

    Contains methods that allow for processing the report into a LaTeX file.
    """
    TARGET_AUDIENCE_CHOICES = [
                ('COMM', 'Community'),
                ('UNIV', 'University'),
                ('PROF', 'Profession'),
                ('CHAP', 'Chapter'),
                ('HON', 'Honors/Awards'),
    ]
    one_to_five = [
                ('1', '1:Best'),
                ('2', '2'),
                ('3', '3'),
                ('4', '4'),
                ('5', '5: Worst')
    ]
    name = models.CharField(max_length=128, verbose_name='Project Name')
    term = models.ForeignKey('mig_main.AcademicTerm')
    relation_to_TBP_objectives = models.TextField()
    is_new_event = models.BooleanField(default=False)
    organizing_hours = models.PositiveSmallIntegerField()
    planning_start_date = models.DateField()
    target_audience = models.CharField(
                            max_length=4,
                            choices=TARGET_AUDIENCE_CHOICES,
                            default='COMM'
    )
    # Contact info:
    contact_name = models.CharField(
                            max_length=75,
                            blank=True
    )
    contact_email = models.EmailField(
                            max_length=254,
                            blank=True
    )
    contact_phone_number = PhoneNumberField(blank=True)
    contact_title = models.CharField(
                            max_length=75,
                            blank=True
    )
    other_info = models.CharField(
                            max_length=150,
                            blank=True
    )
    other_group = models.CharField(
                            max_length=60,
                            blank=True,
    )
    general_comments = models.TextField()
    items = models.TextField()
    cost = models.PositiveIntegerField()
    problems_encountered = models.TextField()
    recommendations = models.TextField()
    evaluations_and_results = models.TextField()
    rating = models.CharField(
                        max_length=1,
                        choices=one_to_five,
                        default='3'
    )
    best_part = models.TextField()
    opportunity_to_improve = models.TextField()
    recommend_continuing = models.BooleanField(default=True)

    def __unicode__(self):
        """
        Returns a unicode representation of the object (its name)
        """
        return self.name

    def get_descriptions(self):
        """
        Returns a string of newline joined descriptions from all of the
        associated events or NonEventProjects.

        Used to show all of the possible descriptions during project report
        generation so that a final one may be chosen.
        """
        has_events = self.calendarevent_set.count() > 0
        if has_events:
            events = self.calendarevent_set.all()
            description = '\n'.join(list(set([e.description for e in events])))
        else:
            neps = self.noneventproject_set.all()
            description = '\n'.join(list(set([n.description for n in neps])))
        return description

    def set_description(self, description):
        """
        Sets the input argument description to be the description of all the
        associated events or NonEventProjects.

        This is used to settle the potentially different descriptions that
        could be entered for events that share a project report.
        """
        has_events = self.calendarevent_set.count() > 0
        if has_events:
            events = self.calendarevent_set.all()
            for event in events:
                event.description = description
                event.save()
        else:
            neps = self.noneventproject_set.all()
            for nep in neps:
                nep.description = description
                nep.save()

    def get_associated_officer(self):
        """ Returns the officer position associated with the project report.

        This is done by looking at the event or the NonEventProject
        information and the associated officer thereof.
        """
        has_events = self.calendarevent_set.exists()
        has_nep = self.noneventproject_set.exists()
        if has_events:
            return self.calendarevent_set.all()[0].assoc_officer
        elif has_nep:
            return self.noneventproject_set.all()[0].assoc_officer
        else:
            return None

    def write_tex_file(self):
        """
        Writes the project report to a .tex file.
        """
        f = open('/tmp/project_report%d.tex' % (self.id), 'w')
        tex_code = self.print_to_tex()
        if tex_code == 0 or tex_code == -1:
            sys.stderr.write('Error printing project report: %d (Error %d)'% (self.id, tex_code))
            return -1
        f.write(tex_code.encode('utf8'))
        f.close()

    def fix_quotes(self, string):
        """
        LaTeX-ifies the quotes in a string by alternately placing left and
        right double quotes.

        This is obviously not perfect, but since the underlying problem is nigh
        unsolveable, this was viewed an acceptable compromise.
        """
        blocks = string.split('\"')
        out_string = blocks[0]
        token = '``'
        for block in blocks[1:]:
            out_string += token
            out_string += block
            if token == '``':
                token = '\"'
            else:
                token = '``'
        return out_string

    def is_url(self, word):
        """ Returns True if the input word is a url.

        This is a heuristic method that tries to determine based on beginnings
        and endings if the word is a url. It is not trying to match any
        potentially valid url, but rather to catch only those words which are
        likely to be used as a url in a project report and could trip up LaTeX.
        """
        if word.startswith('http'):
            return True
        if word.startswith('www.'):
            return True
        if word.count('@') > 0:
            return False
        if (word.endswith('.com') or
           word.endswith('.edu') or
           word.endswith('.org') or
           word.endswith('.gov') or
           word.endswith('.html') or
           word.endswith('.cfm') or
           word.endswith('.htm') or
           word.endswith('.ca') or
           word.endswith('.net')):
            return True
        return False

    def clean_tex_string(self, input_string):
        """
        Escapes the input string for use in a LaTeX document also encloses
        urls.
        """
        output = input_string.replace(r'%', r'''\%''')
        output = output.replace('$', '\\$')
        output = output.replace('&', '\\&')
        output = output.replace('_', '\\_')
        output = output.replace(r'#', r'\#')
        output = self.fix_quotes(output)
        words = output.split()
        count = 0
        while count < len(words):
            word = words[count]
            if self.is_url(word):
                words[count] = r'''\url{'''+word+r'''}'''
            count += 1
        return ' '.join(words)

    def print_to_tex(self):
        """
        Returns the LaTeX code used to generate the project report writeup.

        A unicode-encoded string is returned that can be written into a file
        for the report.
        """
        has_events = self.calendarevent_set.count() > 0
        if has_events:
            events = self.calendarevent_set.all()
            duration = sum([event.get_max_duration().total_seconds()/3600.
                            for event in events])
            if events.count() > 1:
                hours_string = '(Total Duration for %d Events)' % (
                                        events.count()
                )
            else:
                hours_string = '(Event Duration)'
            leaders = MemberProfile.objects.filter(
                            event_leader__in=events).distinct()
            shifts = EventShift.objects.filter(event__in=events).distinct()
            desc = list(set([e.description for e in events]))
            desc_string = '\n'.join(desc)
            all_dates = []
            for shift in shifts:
                all_dates.append(shift.start_time.date())
                all_dates.append(shift.end_time.date())
            all_dates = sorted(list(set(all_dates)))
            date_string = ', '.join([date.strftime('%x')
                                     for date in all_dates])
            if len(all_dates) > 1:
                date_string = 's: ' + date_string
            else:
                date_string = ': ' + date_string
            progress_items = ProgressItem.objects.filter(
                                            related_event__in=events
            )
            progress_items = progress_items.order_by('member').distinct()
            attendees = {}
            active_count = 0
            electee_count = 0
            non_member_count = 0
            for item in progress_items:
                if item.related_event.is_fixed_progress():
                    duration = item.related_event.get_max_duration()
                    scale = Decimal(duration.total_seconds()/3600.)
                    duration = scale
                else:
                    scale = Decimal(1.0)
                if item.member in attendees.keys():
                    attendees[item.member] += scale*item.amount_completed
                else:
                    attendees[item.member] = scale*item.amount_completed
                    if not item.member.init_term == self.term:
                        active_count += 1
                    else:
                        electee_count += 1
            all_attendees = UserProfile.objects.filter(
                                event_attendee__event__in=events).distinct()
            non_members = [member for member in all_attendees
                           if not member.is_member()]
            non_member_count = len(non_members)
            leader_string = r'''Project Leader(%s) (uniqname)\\
            \begin{tabular}{|l|}\hline
            ''' % ('s' if leaders.count > 1 else '')
            for leader in leaders:
                if leader not in attendees:
                    if not leader.init_term == self.term:
                        active_count += 1
                    else:
                        electee_count += 1
                leader_string += r'''%s (%s)\\
                ''' % (leader.get_firstlast_name(), leader.uniqname)
            leader_string += r'''\hline
            \end{tabular}\paraspace
            '''
            attendee_string = r'''\begin{longtable}{|lr|c|r|}\hline
            Name&(uniqname)&Active/Electee/Non-Member&Number of Hours\\ \hline
            \endhead
            \hline
            \endfoot
            '''
            profiles = MemberProfile.objects.filter(
                                        progressitem__in=progress_items
            )
            profiles = profiles.order_by('last_name', 'first_name').distinct()
            for member in profiles:
                status = 'Active'
                if member.init_term == self.term:
                    status = 'Electee'
                attendee_string += r'''%s&(%s)&%s&%.2f\\
                ''' % (member.get_firstlast_name(),
                       member.uniqname,
                       status,
                       attendees[member])
            for non_member in non_members:
                hours = sum([event.get_attendee_hours_at_event(non_member)
                             for event in events])
                attendee_string += r'''%s& (%s) & Non-Member & %.2f\\
                ''' % (non_member.get_firstlast_name(),
                       non_member.uniqname,
                       hours)
            attendee_string += r'\end{longtable}'
            num_part_raw = r'''Active Members:~%d\hspace{.5in}Electees:~%d'''
            num_part_string = num_part_raw % (active_count, electee_count)
            duration_s = '%.1f' % (duration)
        else:
            neps = self.noneventproject_set.all()
            if neps.count() < 1:
                return 0
            if neps.count() > 1:
                return -1
            nep = neps[0]
            date_string = 's: %s--%s ' % (
                                nep.start_date.strftime('%x'),
                                nep.end_date.strftime('%x')
            )
            participants = nep.noneventprojectparticipant_set.all()
            leaders = nep.leaders.all()
            attendees = {}
            active_count = 0
            electee_count = 0
            non_member_count = 0
            for item in participants:
                participant = item.participant
                if participant in attendees.keys():
                    attendees[participant] += item.hours
                else:
                    attendees[participant] = item.hours
                    if not participant.is_member():
                        non_member_count += 1
                    elif not participant.memberprofile.init_term == self.term:
                        active_count += 1
                    else:
                        electee_count += 1
            leader_string = r'''Project Leader(%s) (uniqname)\\
            \begin{tabular}{|l|}\hline
            ''' % ('s' if leaders.count > 1 else '')
            for leader in leaders:
                leader_userprofile = UserProfile.objects.get(
                                            uniqname=leader.uniqname
                )
                if leader_userprofile not in attendees:
                    if not leader.init_term == self.term:
                        active_count += 1
                    else:
                        electee_count += 1
                leader_string += r'''%s (%s)\\
                ''' % (leader.get_firstlast_name(), leader.uniqname)
            leader_string += r'''\hline
            \end{tabular}\paraspace
            '''
            attendee_string = r'''\begin{longtable}{|lr|c|r|}\hline
            Name&(uniqname)&Active/Electee/Non-Member &Number of Hours\\ \hline
            \endhead
            \hline
            \endfoot
            '''
            profiles = UserProfile.objects.filter(
                            noneventprojectparticipant__in=participants
            ).order_by('last_name', 'first_name')
            for member in profiles:
                if not member.is_member():
                    status_string = 'Non-member'
                elif not member.memberprofile.init_term == self.term:
                    status_string = 'Active'
                else:
                    status_string = 'Electee'
                attendee_string += r'''%s&(%s)&%s&%.2f\\
                ''' % (
                        member.get_firstlast_name(),
                        member.uniqname,
                        status_string,
                        attendees[member]
                )
            attendee_string += r'\end{longtable}'
            num_part_raw = r'Active Members:~%d\hspace{.5in}Electees:~%d'
            num_part_string = num_part_raw % (active_count, electee_count)
            desc_string = nep.description
            duration_s = 'N/A'
            hours = [float(attendees[member]) for member in profiles]
            if std(hours) < 0.5:
                duration_s = '%.1f' % median(hours)
            if std(hours) < 0.2:
                hours_string = ''
            else:
                hours_string = 'Varies by participant'

        if self.is_new_event:
            new_project = r'Yes'
        else:
            new_project = r'No'
        if (self.contact_name or
           self.contact_email or
           self.contact_phone_number or
           self.contact_title or
           self.other_info):
            contact_string = r'''\item Contact Information\\
                    \begin{tabular}{l p{5in}}
                    '''
            if self.contact_name:
                contact_string += r'''Name:    &   %s\\
                ''' % (self.contact_name)
            if self.contact_title:
                contact_string += r'''Title:    &   %s\\
                ''' % (self.clean_tex_string(self.contact_title))
            if self.contact_email:
                contact_string += r'''Email:    &   %s\\
                ''' % (self.clean_tex_string(self.contact_email))
            if self.contact_phone_number:
                contact_string += r'''Phone\#:    &   %s\\
                ''' % (self.contact_phone_number)
            if self.other_info:
                contact_string += r'''Other Info:    &   %s\\
                ''' % (self.clean_tex_string(self.other_info))
            contact_string += r'''\end{tabular}
            '''
        else:
            contact_string = ''
        if self.other_group:
            other_group_string = r'''\item Other Organizations Participating: %s
            ''' % (self.other_group)
        else:
            other_group_string = ''
        project_photos = EventPhoto.objects.filter(project_report=self)
        if project_photos.exists():
            picture_string = r'''\item \textbf{Pictures:}
            '''
            for photo in project_photos.order_by('id'):
                picture_string += r'''\begin{figure}[htb]
                \centering
                \includegraphics[max width = .9\textwidth]{%(picture_name)s}
                \caption{%(caption)s}
                \end{figure}
                ''' % {
                    'picture_name': photo.photo.name,
                    'caption': self.fix_quotes(photo.caption)
                }
        else:
            picture_string = ''

        output_string = RAW_TEX_STRING % {
            'project_name': self.name,
            'dates': date_string,
            'planning_date': self.planning_start_date.strftime('%x'),
            'new_project': new_project,
            'participant_numbers': num_part_string,
            'participant_names': leader_string+attendee_string,
            'description': self.clean_tex_string(desc_string),
            'audience': self.get_target_audience_display(),
            'objectives': self.clean_tex_string(
                                self.relation_to_TBP_objectives
            ),
            'contact_string': contact_string,
            'org_hours': self.organizing_hours,
            'part_hours': duration_s,
            'hours_string': hours_string,
            'other_group': other_group_string,
            'gen_comments': self.clean_tex_string(self.general_comments),
            'items': self.clean_tex_string(self.items),
            'cost': self.cost,
            'problems': self.problems_encountered,
            'recommend': self.clean_tex_string(self.recommendations),
            'eval_results': self.clean_tex_string(
                                    self.evaluations_and_results
            ),
            'rating': self.rating,
            'best_part': self.clean_tex_string(self.best_part),
            'improve': self.clean_tex_string(self.opportunity_to_improve),
            'continue': ('Yes' if self.recommend_continuing else 'No'),
            'picture_string': picture_string

        }
        return output_string


class ProjectReportHeader(models.Model):
    """ This is the meta-data object which is used to assemble the report.

    It contains the information needed to compile the physical project report
    information from the individual event summaries.
    """
    executive_summary = models.TextField()
    preparer = models.ForeignKey('mig_main.MemberProfile')
    preparer_title = models.CharField(max_length=128)
    terms = models.ManyToManyField('mig_main.AcademicTerm')

    finished_processing = models.BooleanField(default=False)
    finished_photos = models.BooleanField(default=False)
    last_processed = models.PositiveIntegerField(default=0)
    last_photo = models.PositiveIntegerField(default=0)

    def get_project_reports(self):
        return ProjectReport.objects.filter(term__in=self.terms.all())

    def write_tex_files(self):
        f = open('/tmp/Project_Report_Final_%d.tex' % (self.id), 'w')
        errors = []
        terms = self.terms.all().order_by('year').distinct()
        years = '--'.join([str(term.year) for term in terms])
        print years
        print self.preparer_title
        output_string = RAW_HEADER_STRING % {
            'exec_summary': self.executive_summary,
            'preparer_name': self.preparer.get_firstlast_name(),
            'preparer_title': self.preparer_title,
            'years': years,
        }
        previous_category = 'None'
        officer_files = {}
        officer_sheet_header = r'''
        \documentclass{/srv/www/migweb/static/tex/ProjectReport}
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
        This document contains the project reports related to your officer
        position. Please keep them as reference as and recommendation.\\
        \vfill
        {\large Last revised:}\\
        {\large \today}
        \end{center}
        \end{titlepage}

        '''
        projects = self.get_project_reports().order_by(
                                                'target_audience',
                                                'planning_start_date'
        )
        for project in projects.distinct():
            has_events = project.calendarevent_set.exists()
            has_nep = project.noneventproject_set.exists()
            if not has_events and not has_nep:
                continue
            if not previous_category == project.get_target_audience_display():
                previous_category = project.get_target_audience_display()
                output_string += r'''\part{%s}
                ''' % (previous_category)
            project.write_tex_file()
            asc_off = project.get_associated_officer()
            if asc_off not in officer_files:
                officer_files[asc_off] = {}
            if project.term not in officer_files[asc_off]:
                tmp_file = open(
                        '/tmp/officer_proj_report_%s_%s.tex' % (
                                        project.get_associated_officer().id,
                                        project.term.id
                        ),
                        'w'
                )
                officer_files[asc_off][project.term] = tmp_file
                header_string = officer_sheet_header % {
                            'officer': asc_off.name,
                            'term': unicode(project.term)
                }
                officer_files[asc_off][project.term].write(
                                            header_string.encode('utf8')
                )
            officer_files[asc_off][project.term].write((
                r'''\input{/tmp/project_report%d.tex}%% %s
                \FloatBarrier\newpage\clearpage
                ''' % (project.id, project.name)).encode('utf8'))

            output_string += r'''\input{/tmp/project_report%d.tex}%% %s
            \FloatBarrier\newpage\clearpage''' % (project.id, project.name)
        output_string += r'''\end{document}'''
        cmd = 'xelatex -interaction=nonstopmode %(file_name)s'
        current_dir = os.getcwd()
        os.chdir('/tmp/')
        for officer in officer_files:
            for term in officer_files[officer]:
                end_doc = r'''\end{document}'''.encode('utf8')
                officer_files[officer][term].write(end_doc)
                officer_files[officer][term].close()
                new_cmd = cmd % {
                    'file_name': '/tmp/officer_proj_report_%d_%d.tex' % (
                                        officer.id,
                                        term.id
                    )
                }
                print 'executing: ' + new_cmd
                p = subprocess.Popen(
                                new_cmd.split(' '),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                )
                p_data = p.communicate()
                if p.returncode == 0:
                    p = subprocess.Popen(
                                    new_cmd.split(' '),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                    )
                    p_data = p.communicate()
                    print 'officer compilation successful'
                    comp_proj = CompiledProjectReport.objects.filter(
                                    term=term,
                                    associated_officer=officer
                    )
                    if comp_proj.exists():
                        c = CompiledProjectReport.objects.get(
                                    term=term,
                                    associated_officer=officer
                        )
                    else:
                        c = CompiledProjectReport(
                                term=term,
                                associated_officer=officer,
                                is_full=False
                        )
                        c.save()
                    new_f = open(
                            './officer_proj_report_%d_%d.pdf' % (officer.id,
                                                                 term.id),
                            'r'
                    )
                    c.pdf_file.save('compiled_report_%d.pdf' % c.id,
                                    File(new_f),
                                    True
                                    )
                else:
                    ind_error = {
                        'report': officer.name,
                        'error_code': p.returncode
                    }
                    error_ind = p_data[0].find('!')
                    err_txt = p_data[0][(error_ind-100):(error_ind+250)]
                    ind_error['err'] = '...' + err_txt + '...'
                    errors.append(ind_error)

        f.write(output_string.encode('utf8'))
        f.close()
        new_cmd = cmd % {
                    'file_name': '/tmp/Project_Report_Final_%d.tex' % (self.id)
        }
        p = subprocess.Popen(
                        new_cmd.split(' '),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
        )
        p_data = p.communicate()
        if p.returncode == 0:
            p = subprocess.Popen(
                            new_cmd.split(' '),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
            )
            p.communicate()
            print 'full compilation successful'
            comp_proj = CompiledProjectReport.objects.filter(
                                term=max(self.terms.all()),
                                is_full=True
            )
            if comp_proj.exists():
                c = CompiledProjectReport.objects.get(
                            term=max(self.terms.all()),
                            is_full=True
                )
            else:
                secretary = OfficerPosition.objects.get(name='Secretary')
                c = CompiledProjectReport(
                            term=max(self.terms.all()),
                            is_full=True,
                            associated_officer=secretary
                )
                c.save()
            new_f = open('./Project_Report_Final_%d.pdf' % (self.id), 'r')
            c.pdf_file.save('compiled_report_%d.pdf' % c.id, File(new_f), True)
        else:
            ind_error = {'report': 'Full', 'error_code': p.returncode}
            error_ind = p_data[0].find('!')
            err_txt = p_data[0][(error_ind-100):(error_ind+250)]
            ind_error['err'] = '...' + err_txt + '...'
            errors.append(ind_error)
        os.chdir(current_dir)
        return errors


class OfficerPositionRelationship(models.Model):
    """ Catalogs the evolution of different officer positions.

    This is needed in order to help make sure that officers have access to
    the appropriate reports/transition material even as the officer positions
    change and duties move from one office to another.
    """
    predecessor = models.ForeignKey(
                        'mig_main.OfficerPosition',
                        related_name='officer_relationship_predecessor'
    )
    successor = models.ForeignKey(
                        'mig_main.OfficerPosition',
                        related_name='officer_relationship_successor'
    )
    effective_term = models.ForeignKey('mig_main.AcademicTerm')
    description = models.TextField()

    def __unicode__(self):
        return (unicode(self.predecessor) + '->' +
                unicode(self.successor) + ' in ' +
                unicode(self.effective_term))


class BackgroundCheck(models.Model):
    """ Record of someone having passed a needed background check/training.

    Required for working with minors on campus.
    """
    CHECK_CHOICES = (
        ('U', 'UofM Background Check'),
        ('B', 'BSA Training'),
        ('A', 'AAPS Background Check'),
    )
    member = models.ForeignKey('mig_main.UserProfile')
    date_added = models.DateField(auto_now_add=True)
    check_type = models.CharField(max_length=1, choices=CHECK_CHOICES)

    @classmethod
    def get_valid_checks_for_user(cls, userprofile):
        bu_q = Q(
                date_added__gte=date.today()-timedelta(days=2*365),
                check_type__in=['B', 'U']
        )
        a_q = Q(
                date_added__gte=date.today()-timedelta(days=1*365),
                check_type='A'
        )
        query = bu_q | a_q
        return cls.objects.filter(member=userprofile).filter(query)

    @classmethod
    def user_can_mindset(cls, userprofile):
        valid_checks = cls.get_valid_checks_for_user(userprofile)
        return (valid_checks.filter(check_type='B').exists() and
                valid_checks.filter(check_type='A').exists())

    @classmethod
    def user_can_work_w_minors(cls, userprofile):
        valid_checks = cls.get_valid_checks_for_user(userprofile)
        return (valid_checks.filter(check_type='B').exists() and
                valid_checks.filter(check_type='U').exists())

    def is_valid(self):
        if self.check_type == 'U':
            if (date.today()-self.date_added).days > 2*365:
                return False
            return True
        if self.check_type == 'B':
            if (date.today()-self.date_added).days > 2*365:
                return False
            return True
        if self.check_type == 'A':
            if (date.today()-self.date_added).days > 1*365:
                return False
            return True
        return False
