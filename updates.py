print "processing python updates..."
from event_cal.models import CalendarEvent,EventClass

events = CalendarEvent.objects.filter(event_type__name__in=['Conducted Interviews','Attended Interviews','Undergrad Interviews','Grad Interviews 15','Grad Intervews 30'])
n = 'Electee Interviews'
ec = EventClass.objects.filter(name=n)
if ec.exists():
    ec=ec[0]
else:
    ec=EventClass(name=n)
    ec.save()

for e in events:
    e.event_class=ec
    e.save()

print "finished processing python updates."