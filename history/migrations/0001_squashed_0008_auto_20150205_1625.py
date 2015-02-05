# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import localflavor.us.models
import stdimage.models
import django.db.models.deletion
import history.models
import mig_main.pdf_field
import django.core.validators


class Migration(migrations.Migration):

    replaces = [(b'history', '0001_initial'), (b'history', '0002_auto_20140918_0318'), (b'history', '0003_backgroundcheck'), (b'history', '0004_auto_20140920_0141'), (b'history', '0005_committeemember'), (b'history', '0006_committeemember_member'), (b'history', '0007_auto_20141026_2348'), (b'history', '0008_auto_20150205_1625')]

    dependencies = [
        ('mig_main', '0002_initial_split'),
        ('requirements', '0001_initial'),
        ('mig_main', '0004_committee'),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AwardType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompiledProjectReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_full', models.BooleanField(default=False)),
                ('pdf_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'compiled_project_reports')),
                ('associated_officer', models.ForeignKey(to='mig_main.OfficerPosition')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Distinction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('gift', models.CharField(max_length=128)),
                ('distinction_type', models.ForeignKey(to='requirements.DistinctionType')),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GoverningDocument',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('pdf_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'governing_docs')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GoverningDocumentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MeetingMinutes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pdf_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'minutes')),
                ('meeting_type', models.CharField(default=b'MM', max_length=2, choices=[(b'NI', b'New Initiatives'), (b'MM', b'Main Meetings'), (b'OF', b'Officer Meetings'), (b'AD', b'Advisory Board Meetings'), (b'CM', b'Committee Meeting Minutes')])),
                ('meeting_name', models.CharField(max_length=80)),
                ('display_order', models.PositiveIntegerField()),
                ('semester', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NonEventParticipantAlt',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('participant_name', models.CharField(max_length=128)),
                ('hours', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('participant_status', models.ForeignKey(to='mig_main.Status')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NonEventProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('location', models.CharField(max_length=100, null=True, blank=True)),
                ('assoc_officer', models.ForeignKey(to='mig_main.OfficerPosition')),
                ('leaders', models.ManyToManyField(related_name=b'non_event_project_leader', to=b'mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NonEventProjectParticipant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hours', models.DecimalField(max_digits=5, decimal_places=2, validators=[django.core.validators.MinValueValidator(0)])),
                ('participant', models.ForeignKey(to='mig_main.UserProfile')),
                ('project', models.ForeignKey(to='history.NonEventProject')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Officer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('website_bio', models.TextField()),
                ('website_photo', stdimage.models.StdImageField(upload_to=b'officer_photos')),
                ('position', models.ForeignKey(to='mig_main.OfficerPosition', on_delete=django.db.models.deletion.PROTECT)),
                ('term', models.ManyToManyField(to=b'mig_main.AcademicTerm')),
                ('user', models.ForeignKey(to='mig_main.MemberProfile', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OfficerPositionRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('effective_term', models.ForeignKey(to='mig_main.AcademicTerm')),
                ('predecessor', models.ForeignKey(related_name=b'officer_relationship_predecessor', to='mig_main.OfficerPosition')),
                ('successor', models.ForeignKey(related_name=b'officer_relationship_successor', to='mig_main.OfficerPosition')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name=b'Project Name')),
                ('relation_to_TBP_objectives', models.TextField()),
                ('is_new_event', models.BooleanField(default=False)),
                ('organizing_hours', models.PositiveSmallIntegerField()),
                ('planning_start_date', models.DateField()),
                ('target_audience', models.CharField(default=b'COMM', max_length=4, choices=[(b'COMM', b'Community'), (b'UNIV', b'University'), (b'PROF', b'Profession'), (b'CHAP', b'Chapter'), (b'HON', b'Honors/Awards')])),
                ('contact_name', models.CharField(max_length=75, blank=True)),
                ('contact_email', models.EmailField(max_length=254, blank=True)),
                ('contact_phone_number', localflavor.us.models.PhoneNumberField(max_length=20, blank=True)),
                ('contact_title', models.CharField(max_length=75, blank=True)),
                ('other_info', models.CharField(max_length=150, blank=True)),
                ('other_group', models.CharField(max_length=60, blank=True)),
                ('general_comments', models.TextField()),
                ('items', models.TextField()),
                ('cost', models.PositiveIntegerField()),
                ('problems_encountered', models.TextField()),
                ('recommendations', models.TextField()),
                ('evaluations_and_results', models.TextField()),
                ('rating', models.CharField(default=b'3', max_length=1, choices=[(b'1', b'1:Best'), (b'2', b'2'), (b'3', b'3'), (b'4', b'4'), (b'5', b'5: Worst')])),
                ('best_part', models.TextField()),
                ('opportunity_to_improve', models.TextField()),
                ('recommend_continuing', models.BooleanField(default=True)),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProjectReportHeader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('executive_summary', models.TextField()),
                ('preparer_title', models.CharField(max_length=128)),
                ('finished_processing', models.BooleanField(default=False)),
                ('finished_photos', models.BooleanField(default=False)),
                ('last_processed', models.PositiveIntegerField(default=0)),
                ('last_photo', models.PositiveIntegerField(default=0)),
                ('preparer', models.ForeignKey(to='mig_main.MemberProfile')),
                ('terms', models.ManyToManyField(to=b'mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_published', models.DateField()),
                ('volume_number', models.PositiveSmallIntegerField()),
                ('edition_number', models.PositiveSmallIntegerField()),
                ('name', models.CharField(max_length=70)),
                ('type', models.CharField(default=b'CS', max_length=2, choices=[(b'CS', b'Cornerstone'), (b'AN', b'Alumni News')])),
                ('pdf_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'newsletters')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WebsiteArticle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=250)),
                ('body', models.TextField()),
                ('date_posted', models.DateField()),
                ('approved', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(related_name=b'article_created_by', on_delete=django.db.models.deletion.SET_NULL, to='mig_main.MemberProfile', null=True)),
                ('tagged_members', models.ManyToManyField(related_name=b'article_tagged_members', null=True, to=b'mig_main.MemberProfile', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='noneventproject',
            name='project_report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='history.ProjectReport', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='noneventproject',
            name='term',
            field=models.ForeignKey(default=history.models.default_term, to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='noneventparticipantalt',
            name='project',
            field=models.ForeignKey(to='history.NonEventProject'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='governingdocument',
            name='document_type',
            field=models.ForeignKey(to='history.GoverningDocumentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='award',
            name='award_type',
            field=models.ForeignKey(to='history.AwardType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='award',
            name='recipient',
            field=models.ForeignKey(to='mig_main.MemberProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='award',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='BackgroundCheck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_added', models.DateField(auto_now_add=True)),
                ('check_type', models.CharField(max_length=1, choices=[(b'U', b'UofM Background Check'), (b'B', b'BSA Training'), (b'A', b'AAPS Background Check')])),
                ('member', models.ForeignKey(to='mig_main.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommitteeMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_chair', models.BooleanField(default=False)),
                ('committee', models.ForeignKey(to='mig_main.Committee')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
                ('member', models.ForeignKey(default=None, to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
