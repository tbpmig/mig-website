# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0013_auto_20150121_1337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='completed',
            field=models.BooleanField(default=False, verbose_name=b'Event completed and progress assigned?'),
        ),
    ]
