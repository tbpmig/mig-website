# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import localflavor.us.models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0013_auto_20150927_1121'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookSwapPerson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('UMID', models.CharField(max_length=8, validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{8}$', message=b'Your UMID must be 8 numbers.')])),
                ('address1', models.CharField(max_length=128, null=True, blank=True)),
                ('address2', models.CharField(max_length=128, null=True, blank=True)),
                ('city', models.CharField(max_length=128, null=True, blank=True)),
                ('state', localflavor.us.models.USStateField(blank=True, max_length=2, null=True, choices=[(b'AL', 'Alabama'), (b'AK', 'Alaska'), (b'AS', 'American Samoa'), (b'AZ', 'Arizona'), (b'AR', 'Arkansas'), (b'AA', 'Armed Forces Americas'), (b'AE', 'Armed Forces Europe'), (b'AP', 'Armed Forces Pacific'), (b'CA', 'California'), (b'CO', 'Colorado'), (b'CT', 'Connecticut'), (b'DE', 'Delaware'), (b'DC', 'District of Columbia'), (b'FL', 'Florida'), (b'GA', 'Georgia'), (b'GU', 'Guam'), (b'HI', 'Hawaii'), (b'ID', 'Idaho'), (b'IL', 'Illinois'), (b'IN', 'Indiana'), (b'IA', 'Iowa'), (b'KS', 'Kansas'), (b'KY', 'Kentucky'), (b'LA', 'Louisiana'), (b'ME', 'Maine'), (b'MD', 'Maryland'), (b'MA', 'Massachusetts'), (b'MI', 'Michigan'), (b'MN', 'Minnesota'), (b'MS', 'Mississippi'), (b'MO', 'Missouri'), (b'MT', 'Montana'), (b'NE', 'Nebraska'), (b'NV', 'Nevada'), (b'NH', 'New Hampshire'), (b'NJ', 'New Jersey'), (b'NM', 'New Mexico'), (b'NY', 'New York'), (b'NC', 'North Carolina'), (b'ND', 'North Dakota'), (b'MP', 'Northern Mariana Islands'), (b'OH', 'Ohio'), (b'OK', 'Oklahoma'), (b'OR', 'Oregon'), (b'PA', 'Pennsylvania'), (b'PR', 'Puerto Rico'), (b'RI', 'Rhode Island'), (b'SC', 'South Carolina'), (b'SD', 'South Dakota'), (b'TN', 'Tennessee'), (b'TX', 'Texas'), (b'UT', 'Utah'), (b'VT', 'Vermont'), (b'VI', 'Virgin Islands'), (b'VA', 'Virginia'), (b'WA', 'Washington'), (b'WV', 'West Virginia'), (b'WI', 'Wisconsin'), (b'WY', 'Wyoming')])),
                ('zip', localflavor.us.models.USZipCodeField(max_length=10, null=True, blank=True)),
                ('barcode', models.CharField(unique=True, max_length=256)),
                ('user_profile', models.OneToOneField(to='mig_main.UserProfile')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookSwapStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('selling_enabled', models.BooleanField(default=False)),
                ('receiving_enabled', models.BooleanField(default=False)),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm', unique=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
