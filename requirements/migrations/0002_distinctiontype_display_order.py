# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='distinctiontype',
            name='display_order',
            field=models.PositiveSmallIntegerField(default=0),
            preserve_default=True,
        ),
    ]
