from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from event_cal.models import CalendarEvent

class Command(BaseCommand):
    def handle(self,*args,**options):
        pending_events = CalendarEvent.get_pending_events()
        body_template = r'''Hi %(leaders)s,
This is a friendly reminder that since %(event)s has finished, you now need to assign hours and mark the event as complete. This can be done by visiting https://tbp.engin.umich.edu%(link)s  and following the instructions for completing the event.

Thanks,
The TBP Website'''
        for event in pending_events:
            body=body_template%{'leaders':', '.join([leader.first_name for leader in event.leaders.all()]),'event':event.name,'link':reverse('event_cal:event_detail',args=(event.id,))}
            send_mail('[TBP] A friendly reminder to complete your event.',body,'tbp.mi.g@gmail.com',[leader.get_email() for leader in event.leaders.all()],fail_silently=False)
