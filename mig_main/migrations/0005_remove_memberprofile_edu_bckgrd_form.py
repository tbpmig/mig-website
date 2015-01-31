# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0004_committee'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memberprofile',
            name='edu_bckgrd_form',
        ),
    ]
