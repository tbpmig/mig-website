# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0012_auto_20150115_1733'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendarevent',
            name='preferred_items',
            field=models.TextField(null=True, verbose_name=b'List any (nonobvious) items that attendees should bring, they will be prompted to see if they can.', blank=True),
        ),
        migrations.AlterField(
            model_name='usercanbringpreferreditem',
            name='can_bring_item',
            field=models.BooleanField(default=False, verbose_name=b'Yes, I can bring the item. '),
        ),
    ]
