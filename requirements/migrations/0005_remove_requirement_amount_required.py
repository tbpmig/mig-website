# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0004_auto_20140925_2204'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requirement',
            name='amount_required',
        ),
    ]
