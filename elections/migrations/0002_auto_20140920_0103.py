# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='close_date',
            field=models.DateField(default=datetime.date(2014, 10, 11)),
        ),
        migrations.AlterField(
            model_name='election',
            name='open_date',
            field=models.DateField(default=datetime.date(2014, 9, 20)),
        ),
    ]
