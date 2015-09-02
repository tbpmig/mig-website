# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0011_auto_20150826_2132'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memberprofile',
            name='employer',
        ),
        migrations.RemoveField(
            model_name='memberprofile',
            name='job_field',
        ),
        migrations.RemoveField(
            model_name='memberprofile',
            name='meeting_speak',
        ),
    ]
