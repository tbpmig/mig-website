# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0008_interviewpairing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewpairing',
            name='first_shift',
            field=models.ForeignKey(related_name=b'pairing_first', to='event_cal.EventShift'),
        ),
        migrations.AlterField(
            model_name='interviewpairing',
            name='second_shift',
            field=models.ForeignKey(related_name=b'pairing_second', to='event_cal.EventShift'),
        ),
    ]
