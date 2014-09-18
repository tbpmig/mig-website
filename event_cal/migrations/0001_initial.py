# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import stdimage.models
import django.db.models.deletion
import event_cal.models


class Migration(migrations.Migration):

    dependencies = [
        
    ]

    operations = [
        migrations.CreateModel(
            name='AnnouncementBlurb',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('title', models.CharField(max_length=150)),
                ('text', models.TextField()),
                ('sign_up_link', models.CharField(max_length=128, null=True, blank=True)),
                
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name=b'Event Name')),
                ('description', models.TextField(verbose_name=b'Event Description')),
                ('announce_text', models.TextField(verbose_name=b'Announcement Text')),
                ('announce_start', models.DateField(default=datetime.date.today, verbose_name=b'Date to start including in announcements')),
                ('completed', models.BooleanField(default=False, verbose_name=b'Event and report completed?')),
                ('members_only', models.BooleanField(default=True)),
                ('needs_carpool', models.BooleanField(default=False)),
                ('use_sign_in', models.BooleanField(default=False)),
                ('allow_advance_sign_up', models.BooleanField(default=True)),
                ('needs_facebook_event', models.BooleanField(default=False)),
                ('needs_flyer', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CarpoolPerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(default=b'RI', max_length=2, choices=[(b'DR', b'Driver'), (b'RI', b'Rider')])),
                ('location', models.CharField(default=b'CC', max_length=2, verbose_name=b'Which location is closest to you?', choices=[(b'NC', b'North Campus'), (b'CC', b'Central Campus'), (b'SC', b'South Campus')])),
                ('number_seats', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('event', models.ForeignKey(to='event_cal.CalendarEvent')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('caption', models.TextField(null=True, blank=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'event_photos')),
                ('event', models.ForeignKey(blank=True, to='event_cal.CalendarEvent', null=True)),
                
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventShift',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('location', models.CharField(max_length=100, null=True, blank=True)),
                ('on_campus', models.BooleanField(default=False)),
                ('google_event_id', models.CharField(max_length=64, verbose_name=b'ID for gcal event')),
                ('max_attendance', models.IntegerField(default=None, null=True, blank=True)),
                ('electees_only', models.BooleanField(default=False)),
                ('actives_only', models.BooleanField(default=False)),
                ('grads_only', models.BooleanField(default=False)),
                ('ugrads_only', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='event_cal.CalendarEvent')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GoogleCalendar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('calendar_id', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterviewShift',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('interviewee_shift', models.ForeignKey(related_name=b'shift_interviewee', to='event_cal.EventShift')),
                ('interviewer_shift', models.ForeignKey(related_name=b'shift_interviewer', to='event_cal.EventShift')),

            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MeetingSignIn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code_phrase', models.CharField(max_length=100)),
                ('quick_question', models.TextField()),
                ('event', models.ForeignKey(to='event_cal.CalendarEvent')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MeetingSignInUserData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question_response', models.TextField()),
                ('free_response', models.TextField()),
                ('meeting_data', models.ForeignKey(to='event_cal.MeetingSignIn')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='calendarevent',
            name='google_cal',
            field=models.ForeignKey(to='event_cal.GoogleCalendar'),
            preserve_default=True,
        ),

    ]
