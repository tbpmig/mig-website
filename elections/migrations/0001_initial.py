# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('open_date', models.DateField(default=datetime.date(2014, 9, 18))),
                ('close_date', models.DateField(default=datetime.date(2014, 10, 9))),
                ('officers_for_election', models.ManyToManyField(to='mig_main.OfficerPosition')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Nomination',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('accepted', models.NullBooleanField(default=None)),
                ('election', models.ForeignKey(to='elections.Election')),
                ('nominator', models.ForeignKey(related_name=b'nominator', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mig_main.UserProfile', null=True)),
                ('nominee', models.ForeignKey(related_name=b'nominee', to='mig_main.MemberProfile')),
                ('position', models.ForeignKey(to='mig_main.OfficerPosition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
