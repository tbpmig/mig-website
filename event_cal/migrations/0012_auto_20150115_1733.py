# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0004_committee'),
        ('event_cal', '0011_auto_20150113_1225'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCanBringPreferredItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_bring_item', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='event_cal.CalendarEvent')),
                ('user', models.ForeignKey(to='mig_main.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='preferred_items',
            field=models.TextField(null=True, verbose_name=b'List any items that attendees should bring, they will be prompted to see if they can.', blank=True),
            preserve_default=True,
        ),
    ]
