# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_squashed_0008_auto_20150205_1625'),
    ]

    operations = [
        migrations.AlterField(
            model_name='committeemember',
            name='member',
            field=models.ForeignKey(to='mig_main.MemberProfile'),
        ),
    ]
