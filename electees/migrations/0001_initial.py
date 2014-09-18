# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mig_main.pdf_field


class Migration(migrations.Migration):

    dependencies = [
        ('event_cal', '__first__'),
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackgroundInstitution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name=b'Institution Name')),
                ('degree_type', models.CharField(max_length=16)),
                ('major', models.CharField(max_length=128)),
                ('degree_start_date', models.DateField()),
                ('degree_end_date', models.DateField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EducationalBackgroundForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('degree_type', models.CharField(max_length=16)),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_name', models.CharField(max_length=50, verbose_name=b'Team Name')),
                ('points', models.PositiveSmallIntegerField(default=0)),
                ('leaders', models.ManyToManyField(related_name=b'electee_group_leaders', to='mig_main.MemberProfile')),
                ('members', models.ManyToManyField(related_name=b'electee_group_members', to='mig_main.MemberProfile')),
                ('officers', models.ManyToManyField(related_name=b'electee_group_officers', to='mig_main.MemberProfile')),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeGroupEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('points', models.PositiveSmallIntegerField()),
                ('related_event_id', models.PositiveIntegerField(default=None, null=True, blank=True)),
                ('electee_group', models.ForeignKey(verbose_name=b'Electee Team', to='electees.ElecteeGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeInterviewFollowup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_barrier', models.BooleanField(default=False)),
                ('recommendation', models.CharField(max_length=1, choices=[(b'Y', b'Recommend'), (b'M', b'Not Sure'), (b'N', b'Do not recommend')])),
                ('comments', models.TextField(blank=True)),
                ('interview', models.ForeignKey(to='event_cal.InterviewShift')),
                ('member', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeInterviewSurvey',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('due_date', models.DateField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resource_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'electee_resources')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ElecteeResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('is_packet', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SurveyAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SurveyPart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('number_of_required_questions', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('display_order', models.PositiveSmallIntegerField(default=1)),
                ('visibility', models.CharField(default=b'R', max_length=1, choices=[(b'E', b'Fellow Electees'), (b'A', b'Active Members'), (b'M', b'All Members'), (b'R', b'Only Admins/VPs')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SurveyQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=64)),
                ('text', models.TextField()),
                ('max_words', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('display_order', models.PositiveSmallIntegerField(default=1)),
                ('part', models.ForeignKey(to='electees.SurveyPart')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='question',
            field=models.ForeignKey(to='electees.SurveyQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='submitter',
            field=models.ForeignKey(to='mig_main.MemberProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='surveyanswer',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='electeeresource',
            name='resource_type',
            field=models.ForeignKey(to='electees.ElecteeResourceType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='electeeresource',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='electeeinterviewsurvey',
            name='questions',
            field=models.ManyToManyField(to='electees.SurveyQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='electeeinterviewsurvey',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='backgroundinstitution',
            name='form',
            field=models.ForeignKey(to='electees.EducationalBackgroundForm'),
            preserve_default=True,
        ),
    ]
