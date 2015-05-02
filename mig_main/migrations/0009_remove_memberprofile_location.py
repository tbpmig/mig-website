# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0008_auto_20150502_1138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memberprofile',
            name='location',
        ),
    ]
