# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0005_calendarevent_mutually_exclusive_shifts'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlecalendar',
            name='display_order',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=True,
        ),
    ]
