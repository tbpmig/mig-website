from django.core.management.base import BaseCommand

from event_cal.models import CalendarEvent

class Command(BaseCommand):
    def handle(self,*args,**options):
        CalendarEvent.get_upcoming_events(True)
