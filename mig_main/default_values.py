from django.db import IntegrityError

from mig_main.models import AcademicTerm,CurrentTerm
from requirements.models import SemesterType

#import dbsettings
#class CurrentTerm(dbsettings.Group):
#    current_term_id = dbsettings.PositiveIntegerValue()

def get_current_term():
    current_terms = CurrentTerm.objects.all()
    if current_terms.count()!=1:
        raise IntegrityError('There must be exactly 1 current term object')
    return current_terms[0].current_term
#    return AcademicTerm.objects.get(year=2013, semester_type=SemesterType.objects.get(name='Fall'))
