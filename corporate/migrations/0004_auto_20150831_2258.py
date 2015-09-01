# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0003_auto_20150826_2132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='hq_location',
            field=models.CharField(max_length=256, verbose_name=b'HQ Location'),
        ),
    ]
