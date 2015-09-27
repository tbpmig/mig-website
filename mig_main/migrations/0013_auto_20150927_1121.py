# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0012_auto_20150901_2235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberprofile',
            name='alum_mail_freq',
            field=models.CharField(default=b'WK', max_length=2, verbose_name=b'How frequently would you like alumni emails?', choices=[(b'NO', b'None'), (b'YR', b'Yearly'), (b'SM', b'Semesterly'), (b'MO', b'Monthly'), (b'WK', b'Weekly'), (b'AC', b'Remain Active Member')]),
        ),
    ]
