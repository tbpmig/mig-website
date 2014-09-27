
from django.core.management.base import BaseCommand
from django.utils import timezone

from event_cal.models import EventShift
 
class Command(BaseCommand):
    def handle(self,*args,**options):
        shifts = EventShift.objects.filter(end_time__lte=timezone.localtime(timezone.now()),attendees=None,event__event_type__name='Attended Interviews')
        shifts.delete()
        shifts = EventShift.objects.filter(end_time__lte=timezone.localtime(timezone.now()),attendees=None,event__event_type__name='Conducted Interviews')
        shifts.delete()