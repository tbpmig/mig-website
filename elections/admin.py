from django.contrib import admin
from elections.models import Election, Nomination,TempNomination

class NominationInLine(admin.TabularInline):
	model = Nomination
	extra = 2
	ordering = ['position']

class TempNominationInLine(admin.TabularInline):
	model = TempNomination
	extra = 2
	ordering = ['position']
class ElectionAdmin(admin.ModelAdmin):
	inlines = [TempNominationInLine]
	#list_filter = ['position']
	
admin.site.register(Election,ElectionAdmin)
#admin.site.register(Nomination)
