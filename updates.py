print "processing python updates..."
from event_cal.models import CalendarEvent,EventShift
from mig_main.models import AcademicTerm

# Put the interviews on campus
term=AcademicTerm.get_current_term()
interview_shifts =EventShift.objects.filter(event__term=term,event__event_type__name__contains='Interview')
for shift in interview_shifts:
    shift.on_campus=True
    shift.save()

print "finished processing python updates."