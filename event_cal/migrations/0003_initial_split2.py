# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import stdimage.models
import django.db.models.deletion
import event_cal.models


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0002_initial_split'),
        ('event_cal','0002_initial_split'),
    ]

                
    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='leaders',
            field=models.ManyToManyField(related_name=b'event_leader', to='mig_main.MemberProfile'),
            preserve_default=True,
        ),

        migrations.AddField(
            model_name='calendarevent',
            name='term',
            field=models.ForeignKey(default=event_cal.models.default_term, to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='announcementblurb',
            name='contacts',
            field=models.ManyToManyField(to='mig_main.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='assoc_officer',
            field=models.ForeignKey(to='mig_main.OfficerPosition'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='carpoolperson',
            name='person',
            field=models.ForeignKey(to='mig_main.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventshift',
            name='attendees',
            field=models.ManyToManyField(default=None, related_name=b'event_attendee', null=True, to='mig_main.UserProfile', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventshift',
            name='drivers',
            field=models.ManyToManyField(default=None, related_name=b'event_driver', null=True, to='mig_main.UserProfile', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interviewshift',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
    ]
