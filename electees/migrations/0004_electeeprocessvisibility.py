# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0002_initial_split'),
        ('electees', '0003_electeeinterviewsurvey_instructions'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElecteeProcessVisibility',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('followups_visible', models.BooleanField(default=False)),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
