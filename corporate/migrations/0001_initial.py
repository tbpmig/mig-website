# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mig_main.pdf_field


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CorporateResourceGuide',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=64)),
                ('resource_guide', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=b'corporate_resources')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CorporateTextField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.CharField(default=b'OP', max_length=2, choices=[(b'OP', b'Corporate Involvement Opportunities'), (b'CT', b'Contact'), (b'OT', b'Other')])),
                ('text', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
