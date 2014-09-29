
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.utils import timezone

from electees.models import ElecteeInterviewFollowup
from event_cal.models import InterviewShift
from mig_main.models import AcademicTerm
 
class Command(BaseCommand):
    def handle(self,*args,**options):
        body_template = r'''Hi %(active)s,
This is a friendly reminder that you still need to fill out the post-interview follow-up for your interview with %(interviewee)s.

This can be done by visiting https://tbp.engin.umich.edu%(link)s  and following the instructions for completing the follow-up report.

Thanks,
The TBP Website'''
        interviews = InterviewShift.objects.filter(interviewer_shift__end_time__lte=timezone.localtime(timezone.now()),term=AcademicTerm.get_current_term())
        for interview in interviews.exclude(interviewee_shift__attendees=None):
            for member in interview.interviewer_shift.attendees.all():
                completed_followup = ElecteeInterviewFollowup.objects.filter(interview=interview,member=member).exists()
                if not completed_followup:
                    name = member.get_firstlast_name()
                    interviewee =interview.interviewee_shift.attendees.all()[0].get_firstlast_name()
                    link = reverse('electees:view_my_interview_forms')
                    body=body_template%{'active':name,'interviewee':interviewee,'link':link}
                    send_mail('[TBP] A friendly reminder to complete your interview followups.',body,'tbp.mi.g@gmail.com',[member.get_email()],fail_silently=False)