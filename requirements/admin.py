from django.contrib import admin
from requirements.models import DistinctionType, SemesterType, Requirement, ProgressItem,EventCategory
	
admin.site.register(DistinctionType)
admin.site.register(SemesterType)
admin.site.register(Requirement)
admin.site.register(ProgressItem)
admin.site.register(EventCategory)

#admin.site.register(Nomination)
