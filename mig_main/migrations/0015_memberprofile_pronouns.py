# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

choices = [
  (b'S', b'She/Her'),
  (b'H', b'He/Him'),
  (b'T', b'They/Them'),
  (b'Z', b'Ze/Hir'),
  (b'N', b'No pronouns - Use my name'),
  (b'A', b'Ask me')
]

class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0014_auto_20160103_1812'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pronoun',
            fields=[
                ('pronoun', models.CharField(max_length=60)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='pronouns',
            field=models.ManyToManyField(to='mig_main.Pronoun'),
        )
    ]
