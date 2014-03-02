from django.core.management.base import BaseCommand

from corporate.views import update_resume_zips

class Command(BaseCommand):
    def handle(self,*args,**options):
        update_resume_zips()
