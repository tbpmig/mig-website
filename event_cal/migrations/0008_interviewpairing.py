# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '0007_waitlistslot'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterviewPairing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_shift', models.ForeignKey(related_name=b'shift_first', to='event_cal.EventShift')),
                ('second_shift', models.ForeignKey(related_name=b'shift_second', to='event_cal.EventShift')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
