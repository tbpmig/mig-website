from django.contrib import admin
from history.models import Publication, Officer, WebsiteArticle, ProjectReport, MeetingMinutes, Distinction, GoverningDocumentType, GoverningDocument,AwardType,Award,NonEventProject


admin.site.register(Publication)
admin.site.register(Officer)
admin.site.register(WebsiteArticle)
admin.site.register(ProjectReport)
admin.site.register(MeetingMinutes)
admin.site.register(Distinction)
admin.site.register(GoverningDocumentType)
admin.site.register(GoverningDocument)
admin.site.register(AwardType)
admin.site.register(Award)
admin.site.register(NonEventProject)
