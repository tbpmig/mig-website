# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ForumMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('content', models.TextField()),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('score', models.IntegerField(default=0)),
                ('hidden', models.BooleanField(default=False)),
                ('creator', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ForumThread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('hidden', models.BooleanField(default=False)),
                ('creator', models.ForeignKey(to='mig_main.MemberProfile')),
                ('forum', models.ForeignKey(to='fora.Forum')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MessagePoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plus_point', models.BooleanField(default=False)),
                ('message', models.ForeignKey(to='fora.ForumMessage')),
                ('user', models.ForeignKey(to='mig_main.MemberProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='forummessage',
            name='forum_thread',
            field=models.ForeignKey(to='fora.ForumThread'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='forummessage',
            name='in_reply_to',
            field=models.ForeignKey(related_name=b'replies', blank=True, to='fora.ForumMessage', null=True),
            preserve_default=True,
        ),
    ]
