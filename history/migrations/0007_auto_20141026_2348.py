# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0006_committeemember_member'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meetingminutes',
            name='meeting_type',
            field=models.CharField(default=b'MM', max_length=2, choices=[(b'NI', b'New Initiatives'), (b'MM', b'Main Meetings'), (b'OF', b'Officer Meetings'), (b'AD', b'Advisory Board Meetings'), (b'CM', b'Committee Meeting Minutes')]),
        ),
    ]
