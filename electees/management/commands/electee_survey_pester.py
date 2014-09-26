from datetime import date
from optparse import make_option

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from event_cal.models import CalendarEvent
from electees.models import ElecteeInterviewSurvey
from mig_main.models import MemberProfile,AcademicTerm
from requirements.models import ProgressItem,EventCategory
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--duedate',
            action='store_true',
            dest='duedate',
            default=False,
            help='Specify that this pester is the 8pm on the due date one.'),
        )
    def handle(self,*args,**options):
        term = AcademicTerm.get_current_term()
        current_surveys = ElecteeInterviewSurvey.objects.filter(term = term)
        if current_surveys.exists():
            current_survey=current_surveys[0]
        else:
            return
        until_due = (current_survey.due_date - date.today()).days
        electees = MemberProfile.get_electees()
        for electee in electees:
            completed = current_survey.check_if_electee_completed(electee)
            existing_progress = ProgressItem.objects.filter(member=electee,term=term,event_type__name='Interview Survey')
            if existing_progress.exists() and not completed:
                existing_progress.delete()
            elif completed and not existing_progress.exists():
                p = ProgressItem(member=electee,term=term,amount_completed=1,date_completed=date.today(),name='Interview Survey Completed')
                p.event_type = EventCategory.objects.get(name='Interview Survey')
                p.save()
        if options['duedate']:
            if until_due==1:
                due_date = "Both are due tonight."
            else:
                return
        
        else:
            if until_due == 7 or until_due == 3 or until_due==1:
                due_date = "Both are due %s."%(current_survey.due_date.strftime("%A, %b %d" ))
            
            elif until_due<=0 and until_due>=-7:
                due_date = "Both were due %s."%(current_survey.due_date.strftime("%A, %b %d" ))
            
            else:
                return
        body_template = r'''Hi %(electee)s,
This is a friendly reminder that you still need to finish the electee survey and upload your resume. %(duedate)s

This can be done by visiting https://tbp.engin.umich.edu%(link)s  and following the instructions for completing the survey.
You can upload a resume from your profile page.

Thanks,
The TBP Website'''
        for electee in electees:
            if current_survey.check_if_electee_completed(electee):
                continue
            body=body_template%{'electee':electee.get_firstlast_name(),'link':reverse('electees:complete_survey'),'duedate':due_date}
            send_mail('[TBP] A friendly reminder to complete your survey.',body,'tbp.mi.g@gmail.com',[electee.get_email()],fail_silently=False)
