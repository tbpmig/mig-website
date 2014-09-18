# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import stdimage.models
import mig_main.pdf_field
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0001_initial'),
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='MindSETModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('concepts', models.TextField()),
                ('presentation', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'mindset_module_presentations', blank=True)),
                ('worksheet', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'mindset_module_worksheets', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MindSETProfileAdditions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mindset_bio', models.TextField()),
                ('favorite_ice_cream', models.CharField(max_length=128)),
                ('favorite_city', models.CharField(max_length=128)),
                ('fun_fact', models.TextField()),
                ('user', models.OneToOneField(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutreachEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('banner', stdimage.models.StdImageField(upload_to=b'outreach_event_banners')),
                ('google_form_link', models.CharField(max_length=256, null=True, blank=True)),
                ('pin_to_top', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutreachEventType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('text', models.TextField()),
                ('url_stem', models.CharField(unique=True, max_length=64, validators=[django.core.validators.RegexValidator(regex=b'^[a-z,_]+$', message=b'The url stem must use only the lowercase letters a-z and the underscore.')])),
                ('tab_name', models.CharField(max_length=64, null=True, blank=True)),
                ('has_calendar_events', models.BooleanField(default=True)),
                ('visible', models.BooleanField(default=True)),
                ('event_category', models.ForeignKey(to='requirements.EventCategory', unique=True)),
                ('officers_can_edit', models.ManyToManyField(to='mig_main.OfficerPosition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutreachPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'outreach_photos')),
                ('active', models.BooleanField(default=False)),
                ('title', models.TextField(null=True, blank=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('link', models.CharField(max_length=256, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OutreachPhotoType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TutoringPageSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_title', models.CharField(max_length=128)),
                ('page_content', models.TextField()),
                ('page_order', models.PositiveSmallIntegerField()),
                ('members_only', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TutoringRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_tutored', models.DateField(default=datetime.date.today)),
                ('student_uniqname', models.CharField(max_length=8, verbose_name=b"Tutored student's uniqname", validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b"The tutored student's uniqname must be 3-8 characters, all lowercase.")])),
                ('number_hours', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('courses_tutored', models.TextField()),
                ('topics_covered_and_comments', models.TextField(blank=True)),
                ('approved', models.BooleanField(default=False)),
                ('tutor', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VolunteerFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField(blank=True)),
                ('the_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'mindset_volunteer_files')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='outreachphoto',
            name='photo_type',
            field=models.ForeignKey(to='outreach.OutreachPhotoType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='outreachevent',
            name='outreach_event',
            field=models.ForeignKey(to='outreach.OutreachEventType'),
            preserve_default=True,
        ),
    ]
