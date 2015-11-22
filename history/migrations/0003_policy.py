# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0002_auto_20150205_1630'),
    ]

    operations = [
        migrations.CreateModel(
            name='Policy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('adopted_by', models.CharField(max_length=1, choices=[(b'A', b'Advisory Board'), (b'O', b'Officer Corps'), (b'C', b'Chapter Membership')])),
                ('adopted_date', models.DateField()),
                ('category', models.CharField(max_length=1, choices=[(b'M', b'Membership'), (b'L', b'Leadership'), (b'A', b'Activities'), (b'I', b'Image'), (b'F', b'Finance')])),
                ('effective_until', models.DateField(null=True, blank=True)),
                ('language', models.TextField()),
                ('original_intent', models.TextField(null=True, blank=True)),
                ('scope', models.CharField(max_length=2, choices=[(b'AB', b'Advisory Board'), (b'OC', b'Officer Corps'), (b'OT', b'Individual Officer Team'), (b'IO', b'Individual Officer'), (b'AC', b'Active members'), (b'EL', b'Electees and candidates'), (b'M', b'All members')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
