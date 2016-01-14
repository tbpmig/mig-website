import calendar
import csv
import os
import re
import sys

from datetime import datetime, date, timedelta
from decimal import Decimal


from history.models import NonEventProject, NonEventProjectParticipant
from history.models import ProjectReport, NonEventParticipantAlt, Distinction
from requirements.models import ProgressItem, DistinctionType
from mig_main.models import AcademicTerm, OfficerPosition, Status
from mig_main.models import UserProfile, MemberProfile

cal_dict = {v: k for k, v in enumerate(calendar.month_name)}


def add_da_pa_status_manually(uniqname,
                              distinction,
                              terms,
                              start_term='Fall',
                              start_year='2014'):
    """ Add the active/da/pa status to a member for the given terms.

    Starts at the provided term/year and goes backward adding the statuses
    until it has added a total of 'terms' number of terms. Used for adding in
    information that predates the website.
    """
    user = MemberProfile.objects.get(uniqname=uniqname)
    term = AcademicTerm.objects.get(year=start_year,
                                    semester_type__name=start_term)
    while terms > user.get_num_terms_distinction(distinction):
        if term < user.init_term:
            print uniqname+': ran out of terms'
            break
        if not Distinction.objects.filter(
                                        member=user,
                                        term=term,
                                        distinction_type=distinction
                                        ).exists():
            d = Distinction(member=user,
                            term=term,
                            distinction_type=distinction)
            if distinction.name == 'Active':
                d.gift = 'N/A'
            else:
                d.gift = 'Unknown'
            d.save()
        term = term.get_previous_full_term()
    print 'finished %s %s' % (uniqname, unicode(distinction))


def add_tutoring_to_project_report(id_num, term):
    """ Add the tutoring records from the term to the attendance for the
    provided project report.

    Intended to be used in the project report compilation process. Still needs
    to be added into the workflow.
    """
    pr = NonEventProject.objects.get(id=id_num)
    related_progress = ProgressItem.objects.filter(
                            event_type__name='Tutoring Hours',
                            term=term
                        ).order_by('member').distinct()
    participants = {}
    for progress in related_progress:
        if progress.member in participants:
            participants[progress.member] += progress.amount_completed
        else:
            participants[progress.member] = progress.amount_completed

    for member in participants:
        nepp = NonEventProjectParticipant(project=pr,
                                          participant=member,
                                          hours=participants[member])
        nepp.save()
