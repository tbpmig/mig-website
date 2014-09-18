# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AboutSlideShowPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('photo', stdimage.models.StdImageField(upload_to=b'about_page_photos')),
                ('active', models.BooleanField(default=False)),
                ('title', models.TextField()),
                ('text', models.TextField()),
                ('link', models.CharField(max_length=256, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='JoiningTextField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.CharField(default=b'EL', max_length=2, choices=[(b'EL', b'Eligibility Requirements'), (b'Y', b'Why Join TBP'), (b'UG', b'Requirements to Join (Undergrads)'), (b'GR', b'Requirements to Join (Grads)')])),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
