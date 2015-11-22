print "processing python updates..."
from event_cal.models import CalendarEvent

for e in CalendarEvent.objects.all():
    e.save()

print "finished processing python updates."