from django.contrib import admin
from outreach.models import (
                OutreachPhotoType,
                OutreachPhoto,
                MindSETModule,
                MindSETProfileAdditions,
                TutoringRecord,
                VolunteerFile,
                TutoringPageSection,
                OutreachEventType,
                OutreachEvent,
)

admin.site.register(OutreachPhotoType)
admin.site.register(OutreachPhoto)
admin.site.register(MindSETModule)
admin.site.register(MindSETProfileAdditions)
admin.site.register(TutoringRecord)
admin.site.register(VolunteerFile)
admin.site.register(TutoringPageSection)
admin.site.register(OutreachEventType)
admin.site.register(OutreachEvent)
