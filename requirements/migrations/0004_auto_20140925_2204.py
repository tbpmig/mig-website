# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from decimal import Decimal
from django.db import models, migrations

def transfer_req(apps,schema_editor):
    Requirement = apps.get_model('requirements','Requirement')
    for requirement in Requirement.objects.all():
        requirement.new_amount_required = Decimal(requirement.amount_required)
        requirement.save()
class Migration(migrations.Migration):

    dependencies = [
        ('requirements', '0003_requirement_new_amount_required'),
    ]

    operations = [
        migrations.RunPython(transfer_req),
    ]
