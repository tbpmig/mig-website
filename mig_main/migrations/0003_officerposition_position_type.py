# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0002_initial_split'),
    ]

    operations = [
        migrations.AddField(
            model_name='officerposition',
            name='position_type',
            field=models.CharField(default=b'O', max_length=1, choices=[(b'O', b'Officer'), (b'C', b'Chair')]),
            preserve_default=True,
        ),
    ]
