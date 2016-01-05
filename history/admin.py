from django.contrib import admin
from history.models import (
        Award,
        AwardType,
        CommitteeMember,
        CompiledProjectReport,
        Distinction,
        GoverningDocument,
        GoverningDocumentType,
        MeetingMinutes,
        NonEventProject,
        Officer,
        OfficerPositionRelationship,
        ProjectReport,
        ProjectReportHeader,
        Publication,
        WebsiteArticle,
)


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
admin.site.register(CompiledProjectReport)
admin.site.register(OfficerPositionRelationship)
admin.site.register(ProjectReportHeader)
admin.site.register(CommitteeMember)
