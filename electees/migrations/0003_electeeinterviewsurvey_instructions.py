# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('electees', '0002_surveypart_instructions'),
    ]

    operations = [
        migrations.AddField(
            model_name='electeeinterviewsurvey',
            name='instructions',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
