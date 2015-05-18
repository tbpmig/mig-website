# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0010_memberprofile_location'),
        ('corporate', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('hq_location', models.CharField(max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CorporateEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('mig_alum_text', models.TextField()),
                ('other_tbp_alum_text', models.TextField()),
                ('previous_contact_text', models.TextField()),
                ('salutation', models.CharField(max_length=64)),
                ('subject', models.CharField(max_length=512)),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comments', models.TextField()),
                ('difficulty', models.CharField(max_length=1, choices=[(b'1', b'1: Easy'), (b'2', b'2'), (b'3', b'3: Average'), (b'4', b'4'), (b'5', b'5: Hard')])),
                ('experience', models.CharField(max_length=1, choices=[(b'+', b'Positive'), (b'N', b'Neutral'), (b'-', b'Negative')])),
                ('how_connected', models.CharField(max_length=4, choices=[(b'STCF', b'SWE/TBP Career Fair'), (b'OCF', b'Other Career Fair'), (b'WEB', b'Online Only'), (b'P', b'Personal Contact'), (b'INT', b'Internship/Co-op Conversion')])),
                ('interview_form', models.CharField(max_length=1, choices=[(b'F', b'Phone'), (b'1', b'One-on-one'), (b'P', b'Panel'), (b'G', b'Group')])),
                ('interview_type', models.CharField(max_length=1, choices=[(b'B', b'Behavioral'), (b'T', b'Technical'), (b'+', b'Both'), (b'O', b'Other')])),
                ('job_title', models.CharField(max_length=256)),
                ('location', models.CharField(max_length=1, choices=[(b'P', b'Phone'), (b'S', b'On-site'), (b'C', b'On-campus'), (b'O', b'Other')])),
                ('outcome', models.CharField(blank=True, max_length=1, null=True, choices=[(b'N', b'Not Offered'), (b'D', b'Declined Offer'), (b'A', b'Accepted Offer')])),
                ('company', models.ForeignKey(to='corporate.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InterviewQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.TextField()),
                ('question_type', models.CharField(max_length=1, choices=[(b'B', b'Behavioral'), (b'T', b'Technical'), (b'O', b'Both/Other')])),
                ('company', models.ForeignKey(to='corporate.Company')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobExperience',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('commentary', models.TextField()),
                ('highest_degree', models.CharField(max_length=1, choices=[(b'N', b'None'), (b'B', b'Bachelors'), (b'M', b'Masters'), (b'D', b'Doctorate')])),
                ('region', models.CharField(max_length=2, choices=[(b'MW', b'Midwest'), (b'NE', b'Northeast'), (b'NW', b'Northwest'), (b'SE', b'Southeast'), (b'SW', b'Southwest'), (b'IN', b'International')])),
                ('years', models.PositiveSmallIntegerField(verbose_name=b'If internship, years in school. If fulltime, years with the company')),
                ('overall_rating', models.CharField(max_length=1, choices=[(b'+', b'Positive'), (b'N', b'Neutral'), (b'-', b'Negative')])),
                ('company', models.ForeignKey(to='corporate.Company')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, verbose_name=b'Industry Name')),
                ('majors', models.ManyToManyField(to='mig_main.Major', verbose_name=b'Majors hired in the industry')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JobType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, verbose_name=b'Name of job Type')),
                ('is_full_time', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MemberContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(max_length=256)),
                ('gets_email', models.BooleanField(default=False)),
                ('has_contacted', models.BooleanField(default=False)),
                ('speaking_interest', models.BooleanField(default=False)),
                ('company', models.ForeignKey(to='corporate.Company')),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
                ('personal_contact_of', models.ForeignKey(related_name=b'membercontact_personal_contacts', blank=True, to='mig_main.MemberProfile', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NonMemberContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address', models.CharField(max_length=256)),
                ('gets_email', models.BooleanField(default=False)),
                ('has_contacted', models.BooleanField(default=False)),
                ('speaking_interest', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=256, verbose_name=b'Full name')),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('phone', localflavor.us.models.PhoneNumberField(max_length=20, null=True, blank=True)),
                ('short_bio', models.TextField(null=True, blank=True)),
                ('company', models.ForeignKey(to='corporate.Company')),
                ('initiating_chapter', models.ForeignKey(blank=True, to='mig_main.TBPChapter', null=True)),
                ('personal_contact_of', models.ForeignKey(related_name=b'nonmembercontact_personal_contacts', blank=True, to='mig_main.MemberProfile', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfferDetails',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('commentary', models.TextField()),
                ('highest_degree', models.CharField(max_length=1, choices=[(b'N', b'None'), (b'B', b'Bachelors'), (b'M', b'Masters'), (b'D', b'Doctorate')])),
                ('region', models.CharField(max_length=2, choices=[(b'MW', b'Midwest'), (b'NE', b'Northeast'), (b'NW', b'Northwest'), (b'SE', b'Southeast'), (b'SW', b'Southwest'), (b'IN', b'International')])),
                ('salary', models.PositiveSmallIntegerField(verbose_name=b'Starting Monthly Salary (USD)')),
                ('number_of_vacation_days', models.PositiveSmallIntegerField()),
                ('signing_bonus', models.PositiveSmallIntegerField(verbose_name=b'Signing Bonus (USD)')),
                ('company', models.ForeignKey(to='corporate.Company')),
                ('job_type', models.ForeignKey(to='corporate.JobType')),
                ('major', models.ManyToManyField(to='mig_main.Major')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='jobexperience',
            name='job_type',
            field=models.ForeignKey(to='corporate.JobType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='jobexperience',
            name='major',
            field=models.ManyToManyField(to='mig_main.Major'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interviewquestion',
            name='job_type',
            field=models.ForeignKey(to='corporate.JobType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='interview',
            name='job_type',
            field=models.ForeignKey(to='corporate.JobType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='company',
            name='job_field',
            field=models.ManyToManyField(to='corporate.JobField'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='corporatetextfield',
            name='section',
            field=models.CharField(default=b'OP', unique=True, max_length=2, choices=[(b'OP', b'Corporate Involvement Opportunities'), (b'CT', b'Contact'), (b'OT', b'Other')]),
        ),
    ]
