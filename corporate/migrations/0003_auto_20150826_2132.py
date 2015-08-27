# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('corporate', '0002_auto_20150517_2201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membercontact',
            name='address',
            field=models.CharField(max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='nonmembercontact',
            name='address',
            field=models.CharField(max_length=256, blank=True),
        ),
    ]
