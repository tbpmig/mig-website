# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('bookswap', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FAQItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('text', models.TextField()),
                ('display_order', models.PositiveSmallIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocationImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'bookswap_photos')),
                ('super_caption', models.TextField(null=True, blank=True)),
                ('sub_caption', models.TextField()),
                ('display_order', models.PositiveSmallIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
