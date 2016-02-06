# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0003_policy'),
        ('event_cal', '0020_auto_20151122_1535'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='agenda',
            field=models.ForeignKey(blank=True, to='history.MeetingMinutes', null=True),
            preserve_default=True,
        ),
    ]
