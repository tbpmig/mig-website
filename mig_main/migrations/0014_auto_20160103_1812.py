# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0013_auto_20150927_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='officerposition',
            name='is_elected',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='officerposition',
            name='term_length',
            field=models.CharField(default=b'S', max_length=1, choices=[(b'S', b'Semester'), (b'A', b'Academic Year'), (b'C', b'Calendar year')]),
            preserve_default=True,
        ),
    ]
