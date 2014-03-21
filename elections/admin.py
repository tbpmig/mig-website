from django.contrib import admin
from elections.models import Election, Nomination

class NominationInLine(admin.TabularInline):
	model = Nomination
	extra = 2
	ordering = ['position']

class ElectionAdmin(admin.ModelAdmin):
	inlines = [NominationInLine]
	#list_filter = ['position']
	
admin.site.register(Election,ElectionAdmin)
#admin.site.register(Nomination)
