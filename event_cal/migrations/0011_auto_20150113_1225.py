# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0010_calendarevent_allow_overlapping_sign_ups'),
    ]

    operations = [
        migrations.AddField(
            model_name='calendarevent',
            name='min_sign_up_notice',
            field=models.PositiveSmallIntegerField(default=0, verbose_name=b'Block sign-up how many hours before event starts?'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='min_unsign_up_notice',
            field=models.PositiveSmallIntegerField(default=12, verbose_name=b'Block unsign-up how many hours before event starts?'),
            preserve_default=True,
        ),
    ]
