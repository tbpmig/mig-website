# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0005_remove_memberprofile_edu_bckgrd_form'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='maiden_name',
            field=models.CharField(max_length=40, null=True, blank=True),
            preserve_default=True,
        ),
    ]
