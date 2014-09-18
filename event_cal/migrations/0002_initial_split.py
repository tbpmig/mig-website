# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import stdimage.models
import django.db.models.deletion
import event_cal.models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_auto_20140918_0318'),
        ('requirements', '0001_initial'),
        ('event_cal','0001_initial'),
    ]

                
    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='event_type',
            field=models.ForeignKey(to='requirements.EventCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='project_report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='history.ProjectReport', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventphoto',
            name='project_report',
            field=models.ForeignKey(blank=True, to='history.ProjectReport', null=True),
            preserve_default=True,
        ),
    ]
