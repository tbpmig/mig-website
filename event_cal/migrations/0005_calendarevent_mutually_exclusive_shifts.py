# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0004_auto_20140920_0131'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='mutually_exclusive_shifts',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
