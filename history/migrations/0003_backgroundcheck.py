# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0002_initial_split'),
        ('history', '0002_auto_20140918_0318'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackgroundCheck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateField(auto_now_add=True)),
                ('check_type', models.CharField(max_length=1, choices=[(b'U', b'UofM Background Check'), (b'B', b'BSA Training'), (b'A', b'AAPS Background Check')])),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
