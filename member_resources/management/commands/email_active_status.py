from time import sleep
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from member_resources.quorum import (
        email_active_status
)
from event_cal.models import CalendarEvent

from mig_main.models import MemberProfile, AcademicTerm


class Command(BaseCommand):
    

    def handle(self, *args, **options):
        now = timezone.localtime(timezone.now())
        two_days_from_now = now +timedelta(days=2)
        events = CalendarEvent.objects.filter(
                    earliest_start__gte=now,
                    earliest_start__lte=two_days_from_now,
                    event_type__name='Voting Meeting Attendance',
                    active_status_email_sent=False,
        )
        for event in events:
            email_active_status(event,'Elections' in event.name)
            event.active_status_email_sent=True
            event.save()