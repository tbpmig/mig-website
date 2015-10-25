# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0018_calendarevent_event_class'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='event_class',
            field=models.ForeignKey(verbose_name=b'Choose the event "class" from the list below. If the event is not listed, leave this blank', blank=True, to='event_cal.EventClass', null=True),
        ),
    ]
