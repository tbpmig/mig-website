# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0010_memberprofile_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tbpchapter',
            name='letter',
            field=models.CharField(max_length=4, validators=[django.core.validators.RegexValidator(regex=b'^[A-I,K-U,W-Z]+$', message=b'Greek letter (latin equivalent), e.g. Gammais G, Theta is Q')]),
        ),
        migrations.AlterField(
            model_name='tbpchapter',
            name='state',
            field=models.CharField(max_length=2, validators=[django.core.validators.RegexValidator(regex=b'^[A-Z]{2}$', message=b'Must be the state (or territory) 2-lettercode e.g. Michigan is MI')]),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='uniqname',
            field=models.CharField(max_length=8, serialize=False, primary_key=True, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]{3,8}$', message=b'Your uniqname must be 3-8 characters,all lowercase.')]),
        ),
    ]
