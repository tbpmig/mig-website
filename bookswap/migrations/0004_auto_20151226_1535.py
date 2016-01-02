# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import bookswap.models


class Migration(migrations.Migration):

    dependencies = [
        ('bookswap', '0003_auto_20151226_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookswapcontract',
            name='term',
            field=models.ForeignKey(default=bookswap.models.default_term, to='mig_main.AcademicTerm'),
        ),
    ]
