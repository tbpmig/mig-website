from django.core.management.base import BaseCommand

from corporate.auxiliary_scripts import update_resume_zips
from electees.views import update_electee_resume_zips
class Command(BaseCommand):
    def handle(self,*args,**options):
        update_resume_zips()
        update_electee_resume_zips()
