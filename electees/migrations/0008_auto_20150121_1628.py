# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import electees.models


class Migration(migrations.Migration):

    dependencies = [
        ('electees', '0007_electeeresource_standing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electeeresource',
            name='standing',
            field=models.ForeignKey(default=electees.models.get_default_standing, blank=True, to='mig_main.Standing', null=True),
        ),
    ]
