# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookswap', '0005_auto_20151226_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookswapstatus',
            name='display_prices',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
