# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('electees', '0004_electeeprocessvisibility'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electeeinterviewfollowup',
            name='recommendation',
            field=models.CharField(max_length=1, choices=[(b'Y', b'Recommend'), (b'M', b'Not Sure'), (b'N', b'Do not recommend'), (b'M', b'Missed Interview')]),
        ),
    ]
