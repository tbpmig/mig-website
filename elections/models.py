from datetime import date, timedelta
from django.db import models
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.validators import MaxValueValidator, RegexValidator
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode

from markdown import markdown

from mig_main.models import OfficerPosition

def default_close_date():
    return date.today()+timedelta(weeks=3)


class Election(models.Model):
    """ An election in a given term. This is used mainly to select which
    offices are currently electable and when the nomination period is.
    """
    term = models.ForeignKey('mig_main.AcademicTerm')
    open_date = models.DateField(default=date.today)
    close_date = models.DateField(default=default_close_date)
    officers_for_election = models.ManyToManyField(
                                'mig_main.OfficerPosition',
                                limit_choices_to={'enabled': True}
    )

    def __unicode__(self):
        return str(self.term)+" Election"

    @classmethod
    def get_current_elections(cls):
        return cls.objects.filter(
                        open_date__lte=date.today(),
                        close_date__gte=date.today()
        )

    @classmethod
    def create_election_for_next_term(cls, current_term):
        election = cls(term=current_term.get_next_full_term())
        election.save()
        officers_to_elect = OfficerPosition.objects.filter(
                    enabled=True).filter(is_elected=True)
        if current_term.semester_type.name=='Fall':
            officers_to_elect = officers_to_elect.exclude(term_length='A')
        else:
            officers_to_elect = officers_to_elect.exclude(term_length='C')
            
        election.officers_for_election = officers_to_elect
        election.save()
        return election

class Nomination(models.Model):
    """ A user-submitted nomination for an officer position.
    """
    election = models.ForeignKey(Election)
    nominee = models.ForeignKey(
                        'mig_main.MemberProfile',
                        related_name='nominee'
    )
    nominator = models.ForeignKey(
                        'mig_main.UserProfile',
                        related_name='nominator',
                        null=True,
                        blank=True,
                        on_delete=models.SET_NULL
    )
    position = models.ForeignKey('mig_main.OfficerPosition')
    accepted = models.NullBooleanField(default=None)

    def __unicode__(self):
        name = self.nominee.get_full_name()
        position = self.position.name
        return name + " nominated for " + position

    def email_nominee(self):
        base_web = r'https://tbp.engin.umich.edu/'
        recipient = self.nominee
        recipient_email = recipient.get_email()
        position = self.position
        url_stem = base_web + reverse(
                                'elections:accept_or_decline_nomination',
                                args=(self.id,)
        )
        accept_link = url_stem + r'?accept=YES'
        decline_link = url_stem + r'?accept=NO'
        if position.team_lead.exists():
            leads = ' and '.join(
                            [unicode(x) for x in position.team_lead.all()]
            )
            team_lead_bit = '**Team Lead:** ' + leads
        else:
            team_lead_bit = ''
        if position.team_lead.count() < position.members.count():
            teams = ' and '.join([unicode(x) for x in position.members.all()])
            if position.members.count() > 1:
                team_member_bit = '**Teams:** '
            else:
                team_member_bit = ''
            team_member_bit += teams
        else:
            team_member_bit = ''
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
tbp-elections@umich.edu''' % {
            'name': recipient.get_casual_name(),
            'position': position.name,
            'description': position.description,
            'accept_link': accept_link,
            'decline_link': decline_link,
            'team_info': team_lead_bit + '\n' + team_member_bit
        }
        html_body = markdown(
                        force_unicode(body),
                        ['nl2br'],
                        safe_mode=True,
                        enable_attributes=False
        )
        msg = EmailMultiAlternatives(
                    'You\'ve been nominated for an officer position!',
                    body,
                    'tbp-elections@umich.edu',
                    [recipient_email]
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
