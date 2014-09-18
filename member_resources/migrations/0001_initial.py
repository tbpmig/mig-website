# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uniqname', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b'Uniqnames must be 3-8 characters, all letters')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GradElecteeList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uniqname', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b'Uniqnames must be 3-8 characters, all letters')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectLeaderList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('member_profile', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UndergradElecteeList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uniqname', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b'Uniqnames must be 3-8 characters, all letters')])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
