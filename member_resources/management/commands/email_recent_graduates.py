from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from member_resources.quorum import get_members_who_graduated

from mig_main.models import MemberProfile,AcademicTerm

class Command(BaseCommand):

    def handle(self,*args,**options):
        members_who_graduated = get_members_who_graduated()
        body_template = r'''Hi %(member)s,
It seems as though you've graduated. If so, first, congratulations! Second, please take a moment to update your information on the website to reflect your new alumni status. 
There you'll be able to indicate how often you'd like to be emailed news from the chapter, if you'd be interested in speaking at meetings, etc.

If you haven't yet graduated, please update your profile to reflect a new estimate for your graduation date. 
You can access your profile here:  https://tbp.engin.umich.edu%(profile_link)s

Thanks for your help in keeping our records up-to-date.

Thanks and Forever Go Blue,
The TBP Website'''
        for m in members_who_graduated:
            body=body_template%{'member':m.first_name,'profile_link':reverse('member_resources:profile',args=(m.uniqname,))}
            send_mail('[TBP] Please update website profile.',body,'tbp.mi.g@gmail.com',[m.get_email(),'tbp-website@umich.edu'] ,fail_silently=False)
