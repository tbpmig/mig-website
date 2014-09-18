# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '__first__'),
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='DistinctionType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('standing_type', models.ManyToManyField(to='mig_main.Standing')),
                ('status_type', models.ForeignKey(to='mig_main.Status')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('parent_category', models.ForeignKey(default=None, blank=True, to='requirements.EventCategory', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProgressItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount_completed', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('date_completed', models.DateField()),
                ('name', models.CharField(max_length=100, verbose_name=b'Name/Desciption')),
                ('event_type', models.ForeignKey(to='requirements.EventCategory')),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
                ('related_event', models.ForeignKey(blank=True, to='event_cal.CalendarEvent', null=True)),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
                ('amount_required', models.PositiveSmallIntegerField()),
                ('distinction_type', models.ForeignKey(to='requirements.DistinctionType')),
                ('event_category', models.ForeignKey(to='requirements.EventCategory')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SemesterType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='requirement',
            name='term',
            field=models.ManyToManyField(to='requirements.SemesterType'),
            preserve_default=True,
        ),
    ]
