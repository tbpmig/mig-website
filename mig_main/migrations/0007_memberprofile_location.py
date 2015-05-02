# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mig_main.location_field


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0006_userprofile_maiden_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberprofile',
            name='location',
            field=mig_main.location_field.LocationField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
