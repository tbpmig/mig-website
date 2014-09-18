# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import stdimage.models
import mig_main.models
import localflavor.us.models
import django.db.models.deletion
from django.conf import settings
import mig_main.pdf_field
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0001_initial'),
        ('mig_main', '0001_initial'),
        
    ]

    operations = [
        migrations.AddField(
            model_name='academicterm',
            name='semester_type',
            field= models.ForeignKey(to='requirements.SemesterType'),
            preserve_default=True,
        ),
    ]
