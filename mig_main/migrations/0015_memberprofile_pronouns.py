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
        ('mig_main', '0014_auto_20160103_1812.py'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberprofile',
            name='pronouns',
            field=models.CharField(default=b'A', max_length=1, verbose_name=b'What are your personal pronouns?', choices=choices),
        ),
    ]
