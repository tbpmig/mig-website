# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import electees.models


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0004_committee'),
        ('electees', '0006_auto_20150113_2022'),
    ]

    operations = [
        migrations.AddField(
            model_name='electeeresource',
            name='standing',
            field=models.ForeignKey(default=electees.models.get_default_standing, to='mig_main.Standing'),
            preserve_default=True,
        ),
    ]
