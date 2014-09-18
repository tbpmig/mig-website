# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import history.models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='noneventproject',
            name='term',
            field=models.ForeignKey(default=history.models.default_term, to='mig_main.AcademicTerm'),
        ),
    ]
