# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0003_backgroundcheck'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundcheck',
            name='member',
            field=models.ForeignKey(to='mig_main.UserProfile'),
        ),
    ]
