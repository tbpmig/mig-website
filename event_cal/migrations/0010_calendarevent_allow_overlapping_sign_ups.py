# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0009_auto_20150109_0119'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='allow_overlapping_sign_ups',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
