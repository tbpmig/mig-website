# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0004_committee'),
        ('event_cal', '0006_googlecalendar_display_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaitlistSlot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time_added', models.DateTimeField(auto_now_add=True)),
                ('shift', models.ForeignKey(to='event_cal.EventShift')),
                ('user', models.ForeignKey(to='mig_main.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
