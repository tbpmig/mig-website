# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stdimage.models
import mig_main.models
import localflavor.us.models
import django.db.models.deletion
from django.conf import settings
import mig_main.pdf_field
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1960)])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CurrentTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('current_term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Major',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=60)),
                ('acronym', models.CharField(max_length=10)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfficerPosition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=45)),
                ('description', models.TextField()),
                ('email', models.EmailField(max_length=254)),
                ('enabled', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfficerTeam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('end_term', models.ForeignKey(related_name=b'teams_ending_in_term', blank=True, to='mig_main.AcademicTerm', null=True)),
                ('lead', models.ForeignKey(related_name=b'team_lead', to='mig_main.OfficerPosition')),
                ('members', models.ManyToManyField(related_name=b'members', to='mig_main.OfficerPosition')),
                ('start_term', models.ForeignKey(related_name=b'teams_starting_in_term', to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShirtSize',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=35)),
                ('acronym', models.CharField(max_length=4)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SlideShowPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'home_page_photos')),
                ('active', models.BooleanField(default=False)),
                ('title', models.TextField()),
                ('text', models.TextField()),
                ('link', models.CharField(max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Standing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TBPChapter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(max_length=2, validators=[django.core.validators.RegexValidator(regex=b'^[A-Z]{2}$', message=b'Must be the state (or territory) 2-letter code MI')])),
                ('letter', models.CharField(max_length=4, validators=[django.core.validators.RegexValidator(regex=b'^[A-I,K-U,W-Z]+$', message=b'Greek letter (latin equivalent), e.g. Gamma is G, Theta is Q')])),
                ('school', models.CharField(max_length=70)),
            ],
            options={
                'verbose_name': 'TBP Chapter',
                'verbose_name_plural': 'TBP Chapters',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TBPraise',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('public', models.BooleanField(default=False)),
                ('anonymous', models.BooleanField(default=False)),
                ('approved', models.BooleanField(default=False)),
                ('date_added', models.DateField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preference_type', models.CharField(max_length=64)),
                ('preference_value', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('nickname', models.CharField(max_length=40, blank=True)),
                ('first_name', models.CharField(max_length=40)),
                ('middle_name', models.CharField(max_length=40, blank=True)),
                ('last_name', models.CharField(max_length=40)),
                ('suffix', models.CharField(max_length=15, blank=True)),
                ('title', models.CharField(max_length=20, blank=True)),
                ('uniqname', models.CharField(max_length=8, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b'Your uniqname must be 3-8 characters, all lowercase.')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberProfile',
            fields=[
                ('userprofile_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='mig_main.UserProfile')),
                ('UMID', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{8}$', message=b'Your UMID must be 8 numbers.')])),
                ('alt_email', models.EmailField(max_length=254, verbose_name=b'Alternate email', blank=True)),
                ('jobs_email', models.BooleanField(default=True, verbose_name=b'Receive corporate emails?')),
                ('alum_mail_freq', models.CharField(default=b'WK', max_length=2, verbose_name=b'How frequently would you like alumni emails?', choices=[(b'NO', b'None'), (b'YR', b'Yearly'), (b'SM', b'Semesterly'), (b'MO', b'Monthly'), (b'WK', b'Weekly (left on tbp.all)')])),
                ('job_field', models.CharField(max_length=50, verbose_name=b'What is your job field?', blank=True)),
                ('employer', models.CharField(max_length=60, verbose_name=b'Your employer', blank=True)),
                ('preferred_email', models.CharField(default=b'UM', max_length=3, choices=[(b'UM', b'Umich email'), (b'ALT', b'Alternate email')])),
                ('meeting_speak', models.BooleanField(default=False, verbose_name=b'Are you interested in speaking at a meeting?')),
                ('edu_bckgrd_form', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'grad_background_forms', verbose_name=b'Educational Background Form (Grad Electees only)', blank=True)),
                ('short_bio', models.TextField()),
                ('gender', models.CharField(default=b'O', max_length=1, choices=[(b'F', b'Female'), (b'M', b'Male'), (b'O', b'Other/Prefer not to respond')])),
                ('expect_grad_date', models.DateField(verbose_name=b'Expected graduation date')),
                ('still_electing', models.BooleanField(default=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'member_photos')),
                ('resume', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=mig_main.models.resume_file_name, blank=True)),
                ('phone', localflavor.us.models.PhoneNumberField(max_length=20)),
                ('init_chapter', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Initiating Chapter', to='mig_main.TBPChapter')),
                ('init_term', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Initiation term', to='mig_main.AcademicTerm')),
                ('major', models.ManyToManyField(to='mig_main.Major')),
                ('shirt_size', models.ForeignKey(to='mig_main.ShirtSize', on_delete=django.db.models.deletion.PROTECT)),
                ('standing', models.ForeignKey(to='mig_main.Standing', on_delete=django.db.models.deletion.PROTECT)),
                ('status', models.ForeignKey(to='mig_main.Status', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=('mig_main.userprofile',),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userpreference',
            name='user',
            field=models.ForeignKey(to='mig_main.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tbpraise',
            name='giver',
            field=models.ForeignKey(related_name=b'praise_giver', to='mig_main.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tbpraise',
            name='recipient',
            field=models.ForeignKey(related_name=b'praise_recipient', to='mig_main.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='major',
            name='standing_type',
            field=models.ManyToManyField(to='mig_main.Standing'),
            preserve_default=True,
        ),
    ]
