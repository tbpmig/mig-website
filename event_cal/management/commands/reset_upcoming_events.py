from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.template import  loader
from django.utils import timezone

from event_cal.models import CalendarEvent

class Command(BaseCommand):
    def handle(self,*args,**options):
        now = timezone.localtime(timezone.now())
        upcoming_events=CalendarEvent.get_upcoming_events(True)
        upcoming_html=loader.render_to_string('event_cal/upcoming_events.html',{'upcoming_events':upcoming_events,'now':now})
        cache.set('upcoming_events_html',upcoming_html)
