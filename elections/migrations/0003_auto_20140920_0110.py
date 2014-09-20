# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import elections.models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0002_auto_20140920_0103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='close_date',
            field=models.DateField(default=elections.models.default_close_date),
        ),
        migrations.AlterField(
            model_name='election',
            name='open_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
