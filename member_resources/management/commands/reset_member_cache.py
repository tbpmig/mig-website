from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.template import  loader
from django.utils import timezone

from mig_main.models import MemberProfile

class Command(BaseCommand):
    def handle(self,*args,**options):
        active_html=loader.render_to_string('member_resources/member_list.html',{'members':MemberProfile.get_actives(),'member_type':'Actives'})
        cache.set('active_list_html',active_html)
