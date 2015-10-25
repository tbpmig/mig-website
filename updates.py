print "processing python updates..."
from event_cal.models import CalendarEvent, EventClass
import re
events = CalendarEvent.objects.all()
for e in events:
    s = e.name.split()
    if re.match('(^(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$)|^[0-9]+.?[0-9]*$',s[-1]):
        s=s[0:-1]
    n = ' '.join(s).title()
    ec = EventClass.objects.filter(name=n)
    if ec.exists():
        ec=ec[0]
    else:
        ec = EventClass(name=n)
        ec.save()
    e.event_class=ec
    e.save()

for e in EventClass.objects.all().order_by('name'):
    print e.name

print "finished processing python updates."