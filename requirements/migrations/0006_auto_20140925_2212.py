# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0005_remove_requirement_amount_required'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requirement',
            old_name='new_amount_required',
            new_name='amount_required',
        ),
    ]
