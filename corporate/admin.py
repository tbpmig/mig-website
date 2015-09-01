from django.contrib import admin
from corporate.models import CorporateTextField,CorporateResourceGuide,Company,JobField

admin.site.register(CorporateTextField)
admin.site.register(CorporateResourceGuide)
admin.site.register(Company)
admin.site.register(JobField)
