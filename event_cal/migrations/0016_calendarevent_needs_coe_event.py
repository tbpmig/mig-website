# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0015_remove_eventshift_drivers'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='needs_COE_event',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
