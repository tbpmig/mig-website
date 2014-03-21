from mig_main.default_values import get_current_term
from mig_main.models import OfficerTeam,OfficerPosition,AcademicTerm
from elections.models import Election

def update_officers():

    publicity = OfficerPosition.objects.get(name='Publicity Officer')
    publicity.description=r'''**Term:** 1 Semester

The Publicity officer is in charge of making sure everything TBP does is publicized to the appropriate audience. 

* Send a Weekly Announcements email to Chapter mailing lists every Week 
* Publicize Chapter events to the College and/or University if necessary (in collaboration with officer in charge of event) through COE calendar(s), flyer generation, etc.
* Manages the Chapter's social media accounts (except LinkedIn) to promote external facing TBP events.'''

    publicity.save()



