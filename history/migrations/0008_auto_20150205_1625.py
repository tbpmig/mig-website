# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0007_auto_20141026_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meetingminutes',
            name='display_order',
            field=models.PositiveIntegerField(),
        ),
    ]
