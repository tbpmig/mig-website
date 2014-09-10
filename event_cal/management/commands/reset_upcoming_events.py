from django.core.management.base import BaseCommand
from django.template import RequestContext, loader

from event_cal.models import CalendarEvent

class Command(BaseCommand):
    def handle(self,*args,**options):
        upcoming_events=CalendarEvent.get_upcoming_events(True)
        upcoming_html=loader.get_template('event_cal/upcoming_events.html').render(RequestContext(request,{'upcoming_events':upcoming_events,}))
        cache.set('upcoming_events_html',upcoming_html)
