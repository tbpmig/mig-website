from datetime import date, datetime, timedelta
from markdown import markdown
import json

from django.core.cache import cache
from django.core.mail import EmailMessage, send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Max, Min, Q
from django.utils import timezone
from django.utils.encoding import force_unicode
from stdimage import StdImageField
import tweepy

from event_cal.gcal_functions import get_credentials, get_authorized_http
from event_cal.gcal_functions import get_service
from mig_main.models import AcademicTerm, OfficerPosition, MemberProfile
from mig_main.models import UserProfile
from requirements.models import Requirement
from migweb.settings import DEBUG, twitter_token, twitter_secret

COE_EVENT_EMAIL_BODY = r'''%(salutation)s,

%(intro_text)s

**Contact Information**
Uniqname: %(leader_uniq)s
Full Name: %(leader_name)s
Department: Student Organization
Telephone
Email Address: %(leader_email)s

**Submit a new Request**
Name Of Event: %(event_name)s

**Event Information**
Short Description:
%(blurb)s
Type of Event: %(event_type)s (may not be the same as for the COE calendar)
If Type of Event is 'Other', specify here
Event Date: %(date)s
Start Time: %(start_time)s
End Time: %(end_time)s

Multi-Day Event? Enter Additional Dates + Times:
%(mult_shift)s

Location: %(location)s
RSVP Link (optional):  https://tbp.engin.umich.edu%(event_link)s
Contact Person: Use official contact person
Department/Host: Student Organization

Description of Event:
%(description)s

More information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
'''

COE_EVENT_BODY_CANCEL = r'''%(salutation)s,

The event %(event_name)s is no longer listed as needing a COE Calendar Event.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
'''


# Create your models here.
def default_term():
    """ Returns the current term.

    Fixes a serialization issue that results from circular references in
    migrations.
    """
    try:
        return AcademicTerm.get_current_term().id
    except:
        return 1


class GoogleCalendar(models.Model):
    """ Represents an actual calendar on google calendar.

    This is a mostly infrastructural model that contains the name and calendar
    ID attribute of a calendar that is used by the chapter (currently those
    managed by tbp.mi.g@gmail.com).
    """
    calendar_id = models.CharField(max_length=100)
    display_order = models.PositiveSmallIntegerField(default=0)
    name = models.CharField(max_length=40)

    def __unicode__(self):
        return self.name


class EventClass(models.Model):
    """A type of event.

    Basically, this is a type of event that gets held semester after semester,
    while a CalendarEvent is the particular event that happens on a specified
    date/time. This is used to help group events by type of event.
    """

    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class CalendarEvent(models.Model):
    """ An event on the TBP calendar.

    This class captures the essential bits of the event (without tackling the
    details of time and place). It details what types of requirements the event
    can fill, who the leaders are, whether it has been completed, how to
    publicize it, what term it is during, whether to restrict to members only,
    and more as detailed by the fairly clearly named fields.
    """
    agenda = models.ForeignKey('history.MeetingMinutes', null=True, blank=True)
    allow_advance_sign_up = models.BooleanField(default=True)
    allow_overlapping_sign_ups = models.BooleanField(default=False)
    announce_start = models.DateField(
                    verbose_name='Date to start including in announcements',
                    default=date.today
    )
    announce_text = models.TextField('Announcement Text')
    assoc_officer = models.ForeignKey('mig_main.OfficerPosition')
    completed = models.BooleanField(
                        'Event completed and progress assigned?',
                        default=False
    )
    description = models.TextField('Event Description')
    event_type = models.ForeignKey('requirements.EventCategory')
    event_class = models.ForeignKey(
                        EventClass,
                        verbose_name=('Choose the event \"class\" '
                                      'from the list below. If the event is '
                                      'not listed, leave this blank'),
                        null=True,
                        blank=True,
    )
    google_cal = models.ForeignKey(GoogleCalendar)
    leaders = models.ManyToManyField(
                            'mig_main.MemberProfile',
                            related_name="event_leader"
    )
    members_only = models.BooleanField(default=True)
    min_sign_up_notice = models.PositiveSmallIntegerField(
                        'Block sign-up how many hours before event starts?',
                        default=0
    )
    min_unsign_up_notice = models.PositiveSmallIntegerField(
                        'Block unsign-up how many hours before event starts?',
                        default=12
    )
    mutually_exclusive_shifts = models.BooleanField(default=False)
    name = models.CharField('Event Name', max_length=50)
    needs_carpool = models.BooleanField(default=False)
    needs_COE_event = models.BooleanField(default=False)
    needs_facebook_event = models.BooleanField(default=False)
    needs_flyer = models.BooleanField(default=False)
    preferred_items = models.TextField(
                        ('List any (nonobvious) items that attendees should '
                         'bring, they will be prompted to see if they can.'),
                        null=True,
                        blank=True
    )
    project_report = models.ForeignKey(
                        'history.ProjectReport',
                        null=True,
                        blank=True,
                        on_delete=models.SET_NULL
    )
    requires_AAPS_background_check = models.BooleanField(default=False)
    requires_UM_background_check = models.BooleanField(default=False)
    term = models.ForeignKey('mig_main.AcademicTerm', default=default_term)
    use_sign_in = models.BooleanField(default=False)

    # Static attributes.
    before_grace = timedelta(minutes=-30)
    after_grace = timedelta(hours=1)

    # Shift aggregations to speed querying
    earliest_start = models.DateTimeField(default=datetime.now)
    latest_end = models.DateTimeField(default=datetime.now)

    @classmethod
    def get_current_meeting_query(cls):
        """ Returns a Q object for the query for meetings happening now."""

        now = timezone.localtime(timezone.now())
        query = (
            Q(use_sign_in=True) &
            Q(eventshift__end_time__gte=(now-cls.after_grace)) &
            Q(eventshift__start_time__lte=(now-cls.before_grace))
        )
        return query

    @classmethod
    def get_current_term_events_alph(cls):
        """Returns the current term events ordered alphabetically."""
        current_term = AcademicTerm.get_current_term()
        return cls.get_term_events_alph(current_term)

    @classmethod
    def get_current_term_events_rchron(cls):
        """ Returns the current term events ordered reverse-chronologically."""

        current_term = AcademicTerm.get_current_term()
        return cls.get_term_events_rchron(current_term)

    @classmethod
    def get_events_w_o_reports(cls, term):
        """ Returns a queryset of events in 'term' that lack project reports.

        Finds all events for the given term that have been marked as completed
        but for which there is no project report.
        """
        events = cls.objects.filter(term=term,
                                    project_report=None,
                                    completed=True
                                    )
        return events

    @classmethod
    def get_pending_events(cls):
        """ Returns a queryset of uncompleted events in the past.

        Finds all events where all the shifts have passed but the event is not
        yet marked as completed.
        """
        now = timezone.localtime(timezone.now())
        evts = cls.objects.annotate(latest_shift=Max('eventshift__end_time'))
        return evts.filter(latest_shift__lte=now, completed=False)

    @classmethod
    def get_term_events_alph(cls, term):
        """Returns the provided term's events ordered alphabetically."""

        return cls.objects.filter(term=term).order_by('name')

    @classmethod
    def get_term_events_rchron(cls, term):
        """Returns the provided term's events ordered
        reverse-chronologically.
        """
        evts = cls.objects.filter(term=term)
        an_evts = evts.annotate(earliest_shift=Min('eventshift__start_time'))
        return an_evts.order_by('earliest_shift')

    @classmethod
    def get_upcoming_events(cls, reset=False):
        """ Returns a queryset of upcoming events.

        Returns all events that are upcoming or are happening now and have
        sign-in enabled. In this context 'upcoming' is determined by the event
        start time and the announcement start date. Namely if an event has a
        start time in the future and an announcement start date in the past
        (or present), it is considered upcoming. It is thus possible that some
        events will be incorrectly (albeit intentionally) skipped if they have
        announcement start dates set for after the event commences.

        If reset is False, it pulls the upcoming events from the cache
        (provided they exist in the cache). Otherwise it assembles them from
        the database and stores them in the cache prior to returning.
        """
        upcoming_events = cache.get('upcoming_events', None)
        if upcoming_events and not reset:
            return upcoming_events
        now = timezone.localtime(timezone.now())
        today = date.today()
        non_meeting_query = (
                Q(eventshift__start_time__gte=now) &
                Q(announce_start__lte=today)
        )
        meeting_query = cls.get_current_meeting_query()
        not_officer_meeting = ~Q(event_type__name='Officer Meetings')
        event_pool = cls.objects.filter(
                (non_meeting_query | meeting_query) & not_officer_meeting
        )
        an_evts = event_pool.distinct().annotate(
                    earliest_shift=Min('eventshift__start_time')
        )
        upcoming_events = an_evts.order_by('earliest_shift')
        cache.set('upcoming_events', upcoming_events)
        return upcoming_events

    # Instance Methods, built-ins
    def save(self, *args, **kwargs):
        """ Saves the event. Also clears the cache entry for its ajax."""
        if self.eventshift_set.exists():
            shifts = self.eventshift_set.all()
            self.earliest_start = shifts.order_by('start_time')[0].start_time
            self.latest_end = shifts.order_by('-end_time')[0].end_time
        super(CalendarEvent, self).save(*args, **kwargs)
        cache.delete('EVENT_AJAX'+unicode(self.id))

    def delete(self, *args, **kwargs):
        """ Deletes the event. Also clears the cache entry for its ajax."""
        cache.delete('EVENT_AJAX'+unicode(self.id))
        super(CalendarEvent, self).delete(*args, **kwargs)

    def __unicode__(self):
        """ Returns a string representation of the event.

        For use in the admin or in times the event is interpreted as a string.
        """
        return self.name

    def get_relevant_event_type(self, status, standing):
        """ Returns the event type that the event satisfies.

        For a given status and standing, this determines the type of
        requirement that will be filled by attending this event. Since
        requirements are assumed to be hierarchical, this essentially
        traverses upward until it finds an event category listed in the
        requirements associated with that status and standing. If it finds
        none it assumes that this event won't fill any events and so the
        original event category is used.
        """
        requirements = Requirement.objects.filter(
                        distinction_type__status_type__name=status,
                        distinction_type__standing_type__name=standing,
                        term=self.term.semester_type
        )
        ev_category = self.event_type
        while(not requirements.filter(event_category=ev_category).exists() and
              ev_category.parent_category is not None
              ):
            ev_category = ev_category.parent_category
        return ev_category

    def get_relevant_active_event_type(self):
        """ Returns the event type that matters for an active member.

        Templates don't allow methods to have arguments, so this unfortunately
        bakes the argument into the method name. Determines what event category
        should be displayed for an active member based on their requirements.
        This assumes that all actives have the same requirements regardless of
        Standing. It will break if that changes.
        """
        return self.get_relevant_event_type('Active', 'Undergraduate')

    def get_relevant_ugrad_electee_event_type(self):
        """ Returns the event type that matters for an undergraduate electee.

        Templates don't allow methods to have arguments, so this unfortunately
        bakes the argument into the method name. Determines what event category
        should be displayed for an undergraduate electee based on their
        requirements.
        """
        return self.get_relevant_event_type('Electee', 'Undergraduate')

    def get_relevant_grad_electee_event_type(self):
        """ Returns the event type that matters for a graduate student electee.

        Templates don't allow methods to have arguments, so this unfortunately
        bakes the argument into the method name. Determines what event category
        should be displayed for a graduate student electee based on their
        requirements.
        """
        return self.get_relevant_event_type('Electee', 'Graduate')

    def is_event_type(self, type_name):
        """ Returns True if the event satisfies the event type (name) provided.

        This allows for easy determination of parent/child event categories.
        """
        is_event_type = self.event_type.name == type_name
        event_category = self.event_type
        while (not is_event_type and
               event_category.parent_category is not None
               ):
            event_category = event_category.parent_category
            is_event_type = is_event_type or event_category.name == type_name
        return is_event_type

    def is_meeting(self):
        """ Returns True if the event is a meeting.

        This is for any meeting type that satisfies meeting credit, voting or
        general. It is a convenience function for allowing event type
        determination in templates.
        """
        return self.is_event_type('Meeting Attendance')

    def is_fixed_progress(self):
        """ Returns True if the event is a fixed progress event.

        Fixed progress events are those that the amount of credit accrued does
        not depend on the amount of time spent at the event. These include
        socials and meetings, for instance.
        """
        if self.is_meeting():
            return True
        if self.is_event_type('Social Credits'):
            return True
        return False

    def get_locations(self):
        """ Returns a list of unique locations where the event takes place.

        These are determined by the associated event shifts.
        """
        locations = []
        for shift in self.eventshift_set.all():
            if shift.location in locations:
                continue
            locations.append(shift.location)
        return locations

    def get_start_and_end(self):
        """ Returns a dictionary containing the events start and end times.

        Note that these are different than the shift start and end times in the
        case of a multi-shift event. In general they will not be from the same
        shift.
        """

        output = {"start": None, 'end': None}
        ev = CalendarEvent.objects.filter(id=self.id)
        ev = ev.annotate(start_time=Min('eventshift__start_time'))
        e = ev.annotate(end_time=Max('eventshift__end_time'))
        output['start'] = e[0].start_time
        output['end'] = e[0].end_time
        return output

    def get_attendees_with_progress(self):
        """ Returns a list of those who have received progress for the event.

        Analyzes the ProgressItems and gets a distinct list of attendees.
        """
        return list(set([pr.member for pr in self.progressitem_set.all()]))

    def get_max_duration(self):
        """ Returns the maximum possible event duration.

        Calculates the maximum time that could be spent at the event by
        accounting for overlapping shifts or gaps in shifts.
        """
        shifts = self.eventshift_set.all().order_by('start_time')
        duration = shifts[0].end_time-shifts[0].start_time
        if shifts.count() == 1:
            return duration
        previous_shift = shifts[0]
        end_time = previous_shift.end_time
        start_time = previous_shift.start_time
        duration = timedelta(hours=0)
        for shift in shifts[1:]:
            if shift.start_time < end_time:
                end_time = max(shift.end_time, end_time)
            else:
                duration += end_time-start_time
                end_time = shift.end_time
                start_time = shift.start_time
        duration += end_time-start_time
        return duration

    def get_event_attendees(self):
        """ Return a queryset of all the UserProfiles listed as attendees.

        Uses the reverse look-up to find all the UserProfile objects which are
        related to this event by way of an event shift (event_attendee is the
        related name attribute).
        """
        u = UserProfile.objects.filter(event_attendee__event=self)
        return u.distinct()

    def get_users_who_can_bring_items(self):
        """ If the event has preferred items, returns queryset of those who
        can bring them.

        This uses the UserCanBringPreferredItem class to check for whether a
        member can bring the items.
        """
        item_objects = self.usercanbringpreferreditem_set.filter(
                                can_bring_item=True
        )
        u = UserProfile.objects.filter(
                        usercanbringpreferreditem__in=item_objects
        ).distinct()
        return u

    def get_users_who_cannot_bring_items(self):
        """ If the event has preferred items, returns queryset of those who
        cannot bring them.

        This uses the UserCanBringPreferredItem class to check for whether a
        member can bring the items. Note that if the user does not indicate if
        they are able to bring the item or not, then no object will be created
        and they'll show up in neither list.
        """
        item_objects = self.usercanbringpreferreditem_set.filter(
                                can_bring_item=False
        )
        u = UserProfile.objects.filter(
                        usercanbringpreferreditem__in=item_objects
        ).distinct()
        return u

    def get_attendee_hours_at_event(self, profile):
        """ Returns the number of hours the attendee was at the event.

        Determines how many hours the attendee spent at the event by summing
        the time of all shifts accounting for shifts that are overlapped.
        """
        shifts = self.eventshift_set.filter(attendees=profile)
        n = shifts.count()
        count = 0
        hours = 0
        if not shifts.exists():
            return 0
        if self.is_fixed_progress():
            return 1
        shifts = shifts.order_by('start_time')  # No sense sorting until needed
        while count < n:
            start_time = shifts[count].start_time
            end_time = shifts[count].end_time
            while count < (n-1) and shifts[count+1].start_time < end_time:
                count += 1
                end_time = shifts[count].end_time
            hours += (end_time-start_time).seconds/3600.0
            count += 1
        return hours

    def tweet_event(self, include_hashtag=False):
        """ Sends a tweet about the event from the chapter twitter account.

        If the event is members only or the site is in debug mode then no tweet
        is sent. Also has the option of appending the #UmichEngin hashtag to
        the tweet to help increase views.
        """
        if self.members_only or DEBUG:
            return None
        f = open('/srv/www/twitter.dat', 'r')
        token = json.load(f)
        f.close()
        auth = tweepy.OAuthHandler(twitter_token, twitter_secret)
        auth.set_access_token(token[0], token[1])
        api = tweepy.API(auth)
        start_time = self.get_start_and_end()['start']
        if start_time.minute:
            disp_time = start_time.strftime('%b %d, %I:%M%p')
        else:
            disp_time = start_time.strftime('%b %d, %I%p')
        if include_hashtag:
            hashtag = '\n#UmichEngin'
        else:
            hashtag = ''
        max_name_length = 140-len(disp_time)-25-len(hashtag)-3
        name = self.name
        if len(name) > max_name_length:
            name = name[:(max_name_length-3)]+'...'
        link = 'https://tbp.engin.umich.edu'+reverse(
                    'event_cal:event_detail',
                    args=(self.id,)
        )
        tweet_text = "%(name)s:\n%(time)s\n%(link)s%(hashtag)s" % {
                        'name': name,
                        'time': disp_time,
                        'link': link,
                        'hashtag': hashtag
        }

        api.update_status(tweet_text)

    def notify_publicity(self,
                         needed_flyer=False,
                         needed_facebook=False,
                         needed_coe_event=False,
                         edited=False):
        """ Alerts the publicity officer about the event if needed.

        There are a couple of the event categorizations that require some
        action on the part of the chapter's publicity officer, namely if the
        event needs a Facebook event or if it needs a flyer or possibly other
        such considerations yet to come. If this is the case, then when an
        event is created (or edited) an email is sent to the publicity officer
        advising them of the change. The needed_* arguments are used to advise
        on the previous state of the event so that if an event stops being
        listed as needing something, the appropriate action can be taken.
        """
        pub_officer = OfficerPosition.objects.filter(name='Publicity Officer')
        pres = OfficerPosition.objects.filter(name='President')
        if pub_officer.exists():
            publicity_email = pub_officer[0].email
            if self.needs_flyer:
                if not needed_flyer or not edited:
                    body = r'''Hello Publicity Officer,

An event has been created that requires a flyer to be created.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}
                    send_mail('[TBP] Event Needs Flyer.',
                              body,
                              'tbp.mi.g@gmail.com',
                              [publicity_email],
                              fail_silently=False)
                elif edited:
                    body = r'''Hello Publicity Officer,

An event which needs a flyer was updated.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s
Please ensure that all your information is up-to-date.

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}
                    send_mail('[TBP] Event Needing Flyer was Updated.',
                              body,
                              'tbp.mi.g@gmail.com',
                              [publicity_email],
                              fail_silently=False)
            elif needed_flyer:
                body = r'''Hello Publicity Officer,

An event needing a flyer is no longer listed as needing a flyer.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}
                send_mail('[TBP] Flyer Request Cancelled.',
                          body,
                          'tbp.mi.g@gmail.com',
                          [publicity_email],
                          fail_silently=False)
            if self.needs_facebook_event:
                if not needed_facebook or not edited:
                    body = r'''Hello Publicity Officer,

An event has been created that requires a Facebook event to be created.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}

                    send_mail('[TBP] Event Needs Facebook Event.',
                              body,
                              'tbp.mi.g@gmail.com',
                              [publicity_email],
                              fail_silently=False)
                elif edited:
                    body = r'''Hello Publicity Officer,

An event which requires a Facebook event was updated.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s
Please make any necessary updates to the Facebook event.

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}

                    send_mail('[TBP] Event with Facebook Event was Updated.',
                              body,
                              'tbp.mi.g@gmail.com',
                              [publicity_email],
                              fail_silently=False)
            elif needed_facebook:
                body = r'''Hello Publicity Officer,

An event needing a facebook event is no longer listed as needing one.
The event information can be found at https://tbp.engin.umich.edu%(event_link)s

Regards,
The Website

Note: This is an automated email. Please do not reply to it as responses are
not checked.
''' % {'event_link': reverse('event_cal:event_detail', args=(self.id,))}
                send_mail('[TBP] Facebook Event Request Cancelled.',
                          body,
                          'tbp.mi.g@gmail.com',
                          [publicity_email],
                          fail_silently=False)
            if self.needs_COE_event:
                leaders = self.leaders.all()
                leader1 = leaders[0]
                shifts = self.eventshift_set.order_by('start_time')
                shift = shifts[0]
                recipients = [publicity_email]
                salutation = 'Hello Publicity Officer,'
                if pres.exists():
                    recipients.append(pres[0].email)
                    salutation = 'Hello President and Publicity Officer,'
                ccs = [leader.get_email() for leader in leaders]
                if not needed_coe_event or not edited:
                    body = COE_EVENT_EMAIL_BODY % {
                        'salutation': salutation,
                        'intro_text': ('An event has been created that '
                                       'requires a COE calendar event to be '
                                       'created.\nThe required information is '
                                       'below:'),
                        'leader_uniq': leader1.uniqname,
                        'leader_name': leader1.get_firstlast_name(),
                        'leader_email': leader1.get_email(),
                        'event_name': self.name,
                        'blurb': self.announce_text[:200]+(
                                '...' if len(self.announce_text) > 200 else ''
                        ),
                        'event_type': unicode(self.event_type),
                        'date': shift.start_time.strftime('%d %b %Y'),
                        'start_time': shift.start_time.strftime('%I:%M %p'),
                        'end_time': shift.end_time.strftime('%I:%M %p'),
                        'mult_shift': '\n'.join([
                            shift.start_time.strftime('%d %b %Y %I:%M %p') +
                            ' -- ' +
                            shift.end_time.strftime('%d %b %Y %I:%M %p')
                            for shift in shifts
                        ]),
                        'location': shift.location,
                        'description': self.description,
                        'event_link': reverse(
                                        'event_cal:event_detail',
                                        args=(self.id,)
                        )
                    }

                    subject = '[TBP] Event Needs COE Calendar Event.'
                    email = EmailMessage(
                                subject,
                                body,
                                'tbp.mi.g@gmail.com',
                                recipients,
                                headers={'Reply-To': leader1.get_email()},
                                cc=ccs
                            )
                    email.send()
                elif edited:
                    body = COE_EVENT_EMAIL_BODY % {
                        'salutation': salutation,
                        'intro_text': ('An event has been edited that '
                                       'requires a COE calendar event to be '
                                       'created.\nThe updated information is '
                                       'below:'),
                        'leader_uniq': leader.uniqname,
                        'leader_name': leader.get_firstlast_name(),
                        'leader_email': leader.get_email(),
                        'event_name': self.name,
                        'blurb': self.announce_text[:200]+(
                                '...' if len(self.announce_text) > 200 else ''
                        ),
                        'event_type': unicode(self.event_type),
                        'date': shift.start_time.strftime('%d %b %Y'),
                        'start_time': shift.start_time.strftime('%I:%M %p'),
                        'end_time': shift.end_time.strftime('%I:%M %p'),
                        'mult_shift': '\n'.join([
                            shift.start_time.strftime('%d %b %Y %I:%M %p') +
                            ' -- ' +
                            shift.end_time.strftime('%d %b %Y %I:%M %p')
                            for shift in shifts
                        ]),
                        'location': shift.location,
                        'description': self.description,
                        'event_link': reverse(
                                        'event_cal:event_detail',
                                        args=(self.id,)
                        )
                    }

                    subject = '[TBP] Event Needs COE Calendar Event (updated).'
                    email = EmailMessage(
                                subject,
                                body,
                                'tbp.mi.g@gmail.com',
                                recipients,
                                headers={'Reply-To': leader1.get_email()},
                                cc=ccs
                            )
                    email.send()
            elif needed_coe_event:
                leaders = self.leaders.all()
                leader1 = leaders[0]
                recipients = [publicity_email]
                salutation = 'Hello Publicity Officer,'
                if pres.exists():
                    recipients.append(pres[0].email)
                    salutation = 'Hello President and Publicity Officer,'
                ccs = [leader.get_email() for leader in leaders]
                body = COE_EVENT_BODY_CANCEL % {
                            'salutation': salutation,
                            'event_name': self.name,
                            'event_link': reverse(
                                            'event_cal:event_detail',
                                            args=(self.id,)
                            )
                }
                subject = '[TBP] Event Needs COE Calendar Event (cancelled).'
                email = EmailMessage(
                            subject,
                            body,
                            'tbp.mi.g@gmail.com',
                            recipients,
                            headers={'Reply-To': leader1.get_email()},
                            cc=ccs
                        )
                email.send()

    def email_participants(self, subject, body, sender):
        """ Emails the event participants with the included information.

        Automatically CCs the event leaders. The email is sent by tbp.mi.g but
        the reply-to header is the intended sender's. This is currently due to
        the way email is handled by django/the website.
        """
        attendees = MemberProfile.objects.filter(event_attendee__event=self)
        recipients = [attendee.get_email() for attendee in attendees]
        ccs = [leader.get_email() for leader in self.leaders.all()]

        email = EmailMessage(subject,
                             body,
                             'tbp.mi.g@gmail.com',
                             recipients,
                             headers={'Reply-To': sender.get_email()},
                             cc=ccs)
        email.send()

    def delete_gcal_event(self):
        """ Deletes the event from the associated google calendar.

        Events on the google calendars are actually event shifts, this goes
        through and deletes all of the google calendar events associated with
        this event's shifts.

        If the website is in debug-mode, does nothing.
        """
        if DEBUG:
            return
        c = get_credentials()
        h = get_authorized_http(c)
        if h:
            service = get_service(h)
            for shift in self.eventshift_set.all():
                if shift.google_event_id:
                    try:
                        service.events().delete(
                                    calendarId=self.google_cal.calendar_id,
                                    eventId=shift.google_event_id
                        ).execute()
                    except:
                        pass

    def add_event_to_gcal(self, previous_cal=None):
        """ Adds the event to the associated google calendar.

        Events on the google calendars are actually event shifts, this goes
        through and adds all of the google calendar events associated with
        this event's shifts. If the event previously was associated with
        google calendar events, it attempts to move them to the new calendar
        (if it changed) or to update them. Otherwise (or that failing) it
        creates new events.

        If the website is in debug-mode, does nothing.
        """
        if DEBUG:
            return
        c = get_credentials()
        h = get_authorized_http(c)
        if h:
            service = get_service(h)
            gcal = self.google_cal
            for shift in self.eventshift_set.all():
                new_event = True
                if shift.google_event_id:
                    try:
                        if previous_cal and not (previous_cal == gcal):
                            service.events().move(
                                    calendarId=previous_cal.calendar_id,
                                    eventId=shift.google_event_id,
                                    destination=gcal.calendar_id
                            ).execute()
                        gcal_event = service.events().get(
                                    calendarId=gcal.calendar_id,
                                    eventId=shift.google_event_id
                        ).execute()
                        if gcal_event['status'] == 'cancelled':
                            gcal_event = {}
                            new_event = True
                        else:
                            gcal_event['sequence'] = gcal_event['sequence']+1
                            new_event = False
                    except:
                        gcal_event = {}
                else:
                    gcal_event = {}
                gcal_event['summary'] = self.name
                gcal_event['location'] = shift.location
                gcal_event['start'] = {
                                'dateTime': shift.start_time.isoformat('T'),
                                'timeZone': 'America/Detroit'
                }
                gcal_event['end'] = {
                                'dateTime': shift.end_time.isoformat('T'),
                                'timeZone': 'America/Detroit'
                }
                gcal_event['recurrence'] = []
                gcal_event['description'] = markdown(
                                            force_unicode(self.description),
                                            ['nl2br'],
                                            safe_mode=True,
                                            enable_attributes=False
                )
                if not new_event:
                    service.events().update(
                                    calendarId=gcal.calendar_id,
                                    eventId=shift.google_event_id,
                                    body=gcal_event
                    ).execute()
                else:
                    submitted_event = service.events().insert(
                                    calendarId=gcal.calendar_id,
                                    body=gcal_event
                    ).execute()
                    shift.google_event_id = submitted_event['id']
                    shift.save()

    def can_complete_event(self):
        """ Returns True if the event is able to be marked 'complete'.

        If the event is already completed or has shifts not yet finished,
        it cannot be completed. Otherwise it can be.
        """
        s = self.eventshift_set
        now = timezone.now()
        s_future = s.filter(end_time__gte=now)
        if self.completed:
            return False
        if s_future:
            return False
        else:
            return True

    def does_shift_overlap_with_users_other_shifts(self, shift, profile):
        """ Checks if the given shift overlaps with the profile's other shifts.

        If a user is signed up for multiple shifts, this checks to see if the
        given shift overlaps with any of the other shifts. It is used to
        prevent users from signing up for shifts that overlap if this behavior
        is not intended.
        """
        attendee_shifts = self.eventshift_set.filter(attendees__in=[profile])
        overlapping_q1 = Q(start_time__lt=shift.start_time,
                           end_time__lte=shift.end_time)
        overlapping_q2 = Q(start_time__gte=shift.end_time,
                           end_time__gt=shift.end_time)
        query = overlapping_q1 | overlapping_q2
        overlapping_shifts = attendee_shifts.distinct().exclude(query)
        return overlapping_shifts.exists()

    def get_fullness(self):
        """Gives a trinary evaluation of the fullness of the event.

        Currently only works for single-shift events. Returns one of:
        - Almost empty
        - Nearly full
        - Not full
        depending on how many people have signed up relative to the maximum
        attendance listed.
        """
        shifts = self.eventshift_set.all()
        if shifts.count() > 1:
            return ''
        shift = shifts[0]
        num_attendees = 1.0*shift.attendees.count()
        if shift.max_attendance is None:
            if num_attendees < 5:
                return '(Almost empty)'
            else:
                return '(Not full)'
        elif shift.max_attendance:
            frac_full = num_attendees/shift.max_attendance
            num_spots = shift.max_attendance - num_attendees
            if frac_full > .8 or num_spots <= 1:
                return '(Nearly full)'
            elif frac_full < .2:
                return '(Almost empty)'
            else:
                return '(Not full)'
        else:
            return ''


class EventShift(models.Model):
    """ An event's shift on the TBP Calendar.

    Users sign up for events at the shift level (as an event may have users
    sign up for multiple separate fractions of the total event). Shifts
    capture the time and location information of the event for each possible
    shift and also manage the signing up for the event itself.
    """
    event = models.ForeignKey(CalendarEvent)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=100, blank=True, null=True)
    on_campus = models.BooleanField(default=False)
    google_event_id = models.CharField('ID for gcal event', max_length=64)
    max_attendance = models.IntegerField(null=True, blank=True, default=None)
    attendees = models.ManyToManyField('mig_main.UserProfile',
                                       related_name="event_attendee",
                                       blank=True, default=None)
    electees_only = models.BooleanField(default=False)
    actives_only = models.BooleanField(default=False)
    grads_only = models.BooleanField(default=False)
    ugrads_only = models.BooleanField(default=False)

    def __unicode__(self):
        """ Gives a string representation of the event shift."""
        u = "%(name)s shift from %(start)s--%(end)s" % {
                        'name': self.event.name,
                        'start': str(self.start_time),
                        'end': str(self.end_time),
        }
        return u

    def save(self, *args, **kwargs):
        """ Saves the shift (likely to the database).

        Also deletes the event's ajax entry from the cache to force a refresh.
        """
        super(EventShift, self).save(*args, **kwargs)
        cache.delete('EVENT_AJAX'+unicode(self.event.id))

    def delete(self, *args, **kwargs):
        """ Deletes the shift from the database.

        Also deletes the event's ajax entry from the cache to force a refresh.
        """
        cache.delete('EVENT_AJAX'+unicode(self.event.id))
        super(EventShift, self).delete(*args, **kwargs)

    def is_full(self):
        """ Returns True if the shift cannot accept more attendees."""
        if self.max_attendance is None:
            return False
        if self.attendees.count() >= self.max_attendance:
            return True
        return False

    def is_now(self):
        """ Returns True if the shift is currently happening.

        This takes the before and after grace periods into account.
        """
        now = timezone.now()
        if now > (self.start_time + self.event.before_grace):
            if now < (self.end_time + self.event.after_grace):
                return True
        return False

    def is_before_start(self):
        """ Returns True if the shift has not yet started.

        Does NOT account for the grace period.
        """
        now = timezone.now()
        if now > self.start_time:
            return False
        return True

    def can_sign_in(self):
        """ Returns True if the shift is currently accepting sign-ins."""
        if (self.event.use_sign_in and
           not self.is_full() and
           self.is_now()):
            return True
        return False

    def can_sign_up(self):
        """ Returns True if the shift is accepting advance sign-ups."""
        if (self.event.allow_advance_sign_up and
           not self.is_full() and
           self.is_before_start()):
            return True
        return False

    def get_restrictions(self):
        """ Returns a string representation of the sign up restrictions for the
        shift.
        """
        res_string = ''
        if self.ugrads_only:
            res_string += 'Undergrad'
        if self.grads_only:
            res_string += 'Grad'
        if self.electees_only:
            res_string += ' Electee'
        if self.actives_only:
            res_string += ' Active'
        if not res_string:
            return None
        return res_string.lstrip()+'s'

    def delete_gcal_event_shift(self):
        """ Deletes the google calendar event associated with the shift.

        If in debug mode, does nothing.
        """
        if DEBUG:
            return
        c = get_credentials()
        h = get_authorized_http(c)
        if h:
            event = self.event
            service = get_service(h)
            if self.google_event_id:
                try:
                    service.events().delete(
                        calendarId=event.google_cal.calendar_id,
                        eventId=self.google_event_id
                    ).execute()
                except:
                    pass

    def add_attendee_to_gcal(self, name, email):
        """ Adds the attendee defined by the name and email to the google
        calendar event.

        If in debug mode, does nothing.
        """
        if DEBUG:
            return
        c = get_credentials()
        h = get_authorized_http(c)
        if h:
            service = get_service(h)
            event = self.event
            if not self.google_event_id:
                return
            gcal_event = service.events().get(
                            calendarId=event.google_cal.calendar_id,
                            eventId=self.google_event_id
            ).execute()
            if gcal_event['status'] == 'cancelled':
                return
            else:
                gcal_event['sequence'] += 1
                if 'attendees' in gcal_event:
                    gcal_event['attendees'].append(
                        {
                            'email': email,
                            'displayName': name,
                        })
                else:
                    gcal_event['attendees'] = [{
                            'email': email,
                            'displayName': name,
                        }]
                service.events().update(
                        calendarId=event.google_cal.calendar_id,
                        eventId=self.google_event_id,
                        body=gcal_event
                ).execute()

    def delete_gcal_attendee(self, email):
        """ Removes the attendee, defined by the given email, from the
        associated google calendar event.

        If in debug mode, does nothing.
        """
        if DEBUG:
            return
        c = get_credentials()
        h = get_authorized_http(c)
        if h:
            service = get_service(h)
            event = self.event
            if not self.google_event_id:
                return
            try:
                gcal_event = service.events().get(
                                calendarId=event.google_cal.calendar_id,
                                eventId=self.google_event_id
                ).execute()
                if gcal_event['status'] == 'cancelled':
                    return
                else:
                    gcal_event['sequence'] += 1
                    if 'attendees' in gcal_event:
                        gcal_event['attendees'][:] = [
                                a for a
                                in gcal_event['attendees']
                                if a.get('email') != email
                        ]
                        service.events().update(
                                calendarId=event.google_cal.calendar_id,
                                eventId=self.google_event_id,
                                body=gcal_event
                        ).execute()
            except:
                return

    def get_ordered_waitlist(self):
        """ Get the wait list slot objects associated with the shift in order
        by the time they were added, that is in a normal wait list order.
        """
        return self.waitlistslot_set.all().order_by('time_added')

    def get_waitlist_length(self):
        """ Return the number of users on the waitlist."""
        return self.waitlistslot_set.count()

    def get_users_waitlist_spot(self, profile):
        """ Returns the provided profile's spot on the waitlist."""
        user_waitlist = WaitlistSlot.objects.filter(shift=self, user=profile)
        if not user_waitlist:
            return self.get_waitlist_length()
        w = WaitlistSlot.objects.filter(
                    shift=self,
                    time_added__lt=user_waitlist[0].time_added
        )
        return w.count()

    def get_users_on_waitlist(self):
        """ Return an unordered list of users on the waitlist."""
        waitlist = self.waitlistslot_set.all()
        return UserProfile.objects.filter(waitlistslot__in=waitlist)


class InterviewShift(models.Model):
    """ The object that connects the shift an electee signs up for to be
    interviewed with the shift an active signs up for to be the interviewer.
    """
    interviewer_shift = models.ForeignKey(
                                EventShift,
                                related_name='shift_interviewer'
    )
    interviewee_shift = models.ForeignKey(
                                EventShift,
                                related_name='shift_interviewee'
    )
    term = models.ForeignKey('mig_main.AcademicTerm')

    def user_can_followup(interview, user):
        """ True if the user is able to submit followup for this interview.

        Checks if the user is an interviewer for this interview and also if
        the shift has already started. Followups can be submitted during the
        shift.
        """
        if (not hasattr(user, 'userprofile') or
           not user.userprofile.is_member()):
            return False
        if user.userprofile not in interview.interviewer_shift.attendees.all():
            return False
        if interview.interviewer_shift.start_time >= timezone.now():
            return False
        return True


class MeetingSignIn(models.Model):
    """ Defines the meeting sign-in questionnaire for a meeting. """
    event = models.ForeignKey(CalendarEvent)
    code_phrase = models.CharField(max_length=100)
    quick_question = models.TextField()


class MeetingSignInUserData(models.Model):
    """ The actual data that users provide when signing into a meeting."""
    meeting_data = models.ForeignKey(MeetingSignIn)
    question_response = models.TextField()
    free_response = models.TextField()


class AnnouncementBlurb(models.Model):
    """ A piece of the weekly announcements.

    Compiled together, these form the weekly announcements, along with the
    information about upcoming events.
    """
    start_date = models.DateField()
    end_date = models.DateField()
    title = models.CharField(max_length=150)
    text = models.TextField()
    contacts = models.ManyToManyField('mig_main.UserProfile')
    sign_up_link = models.CharField(max_length=128, blank=True, null=True)

    @classmethod
    def get_current_blurbs(cls):
        """Return a queryset of blurbs to include in today's announcements."""
        now = timezone.localtime(timezone.now())
        return cls.objects.filter(
                    start_date__lte=now.date,
                    end_date__gt=now.date
        )

    def __unicode__(self):
        """ Return a string representation of the  blurb."""
        return self.title


class EventPhoto(models.Model):
    """ A wrapper for a photo that should be saved. Principally used to
    document chapter events and to include in the yearly chapter survey.
    """
    event = models.ForeignKey(CalendarEvent, blank=True, null=True)
    project_report = models.ForeignKey(
                        'history.ProjectReport',
                        blank=True,
                        null=True
    )
    caption = models.TextField(blank=True, null=True)
    photo = StdImageField(upload_to='event_photos',
                          variations={'thumbnail': (800, 800)}
                          )


class CarpoolPerson(models.Model):
    """ A person participating in the carpool. Combines the event, person, and
    information about role, car, etc. into one model.
    """
    event = models.ForeignKey(CalendarEvent)
    person = models.ForeignKey('mig_main.UserProfile')
    ROLES_CHOICES = (
            ('DR', 'Driver'),
            ('RI', 'Rider'),
    )
    LOCATION_CHOICES = (
            ('NC', 'North Campus'),
            ('CC', 'Central Campus'),
            ('SC', 'South Campus'),
    )
    role = models.CharField(max_length=2,
                            choices=ROLES_CHOICES,
                            default='RI')
    location = models.CharField('Which location is closest to you?',
                                max_length=2,
                                choices=LOCATION_CHOICES,
                                default='CC'
                                )
    number_seats = models.PositiveSmallIntegerField(null=True, blank=True)


class WaitlistSlot(models.Model):
    """ A slot on an event shift's waitlist. Collectively these form the
    waitlist.
    """
    shift = models.ForeignKey(EventShift)
    time_added = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('mig_main.UserProfile')


class InterviewPairing(models.Model):
    """ A pairing between shifts of an interview. Intended for streamlining
    sign-up for two-part interviews.
    """
    first_shift = models.ForeignKey(EventShift, related_name='pairing_first')
    second_shift = models.ForeignKey(EventShift, related_name='pairing_second')


class UserCanBringPreferredItem(models.Model):
    """ A note indicating whether a user can bring the preferred item for a
    particular event.
    """
    event = models.ForeignKey(CalendarEvent)
    user = models.ForeignKey('mig_main.UserProfile')
    can_bring_item = models.BooleanField(
                        verbose_name='Yes, I can bring the item. ',
                        default=False
    )
