# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0019_auto_20151024_2033'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='earliest_start',
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='latest_end',
            field=models.DateTimeField(default=datetime.datetime.now),
            preserve_default=True,
        ),
    ]
