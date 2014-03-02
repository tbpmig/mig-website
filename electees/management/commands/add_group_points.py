from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.utils import timezone

from electees.models import ElecteeGroup
from mig_main.default_values import get_current_term

class Command(BaseCommand):
    def handle(self,*args,**options):
        e_groups = ElecteeGroup.objects.filter(term=get_current_term())
        for group in e_groups:
            group.get_points()
