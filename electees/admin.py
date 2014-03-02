from django.contrib import admin
from electees.models import ElecteeGroup, ElecteeGroupEvent,ElecteeResourceType,ElecteeResource,EducationalBackgroundForm,BackgroundInstitution

class ElecteeGroupEventInLine(admin.StackedInline):
	model = ElecteeGroupEvent
	extra = 1

class ElecteeGroupAdmin(admin.ModelAdmin):
	inlines = [ElecteeGroupEventInLine]
	
class BackgroundInstitutionInLine(admin.StackedInline):
    model = BackgroundInstitution
    extra = 1

class EducationalBackgroundFormAdmin(admin.ModelAdmin):
    inlines = [BackgroundInstitutionInLine]

admin.site.register(ElecteeGroup,ElecteeGroupAdmin)
admin.site.register(ElecteeResourceType)
admin.site.register(ElecteeResource)
admin.site.register(EducationalBackgroundForm,EducationalBackgroundFormAdmin)
#admin.site.register(Nomination)
