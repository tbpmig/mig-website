# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mig_main.pdf_field
import bookswap.models


class Migration(migrations.Migration):

    dependencies = [
        ('mig_main', '0013_auto_20150927_1121'),
        ('bookswap', '0002_faqitem_locationimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('price', models.PositiveSmallIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookSwapContract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contract_file', mig_main.pdf_field.ContentTypeRestrictedFileField(upload_to=bookswap.models.contract_file_name, blank=True)),
                ('type', models.CharField(default=b'S', max_length=1, choices=[(b'S', b'Seller'), (b'B', b'Buyer')])),
                ('term', models.ForeignKey(to='mig_main.AcademicTerm')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.CharField(max_length=256, null=True, blank=True)),
                ('edition', models.CharField(max_length=64, null=True, blank=True)),
                ('isbn', models.CharField(max_length=32)),
                ('title', models.CharField(max_length=256)),
                ('course', models.CharField(max_length=128, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='book',
            name='book_type',
            field=models.ForeignKey(to='bookswap.BookType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='buyer',
            field=models.ForeignKey(related_name=b'books_bought', blank=True, to='bookswap.BookSwapPerson', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='seller',
            field=models.ForeignKey(related_name=b'books_sold', to='bookswap.BookSwapPerson'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='term',
            field=models.ForeignKey(to='mig_main.AcademicTerm'),
            preserve_default=True,
        ),
    ]
