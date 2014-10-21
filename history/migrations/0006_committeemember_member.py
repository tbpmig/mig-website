# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0004_committee'),
        ('history', '0005_committeemember'),
    ]

    operations = [
        migrations.AddField(
            model_name='committeemember',
            name='member',
            field=models.ForeignKey(default=None, to='mig_main.MemberProfile'),
            preserve_default=False,
        ),
    ]
