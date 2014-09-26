# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0002_distinctiontype_display_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='requirement',
            name='new_amount_required',
            field=models.DecimalField(default=0.0, max_digits=5, decimal_places=2),
            preserve_default=True,
        ),
    ]
