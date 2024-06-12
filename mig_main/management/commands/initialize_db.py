from django.core.management.base import BaseCommand
from migweb.initializeDB import initializedb

class Command(BaseCommand):
    def handle(self,*args,**options):
        initializedb()
