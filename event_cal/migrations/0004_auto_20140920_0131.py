# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0003_initial_split2'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='requires_AAPS_background_check',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='requires_UM_background_check',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
