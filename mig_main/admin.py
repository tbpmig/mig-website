from django.contrib import admin
from mig_main.models import UserProfile, OfficerPosition, Standing, Status, Major, ShirtSize, TBPChapter, AcademicTerm, OfficerTeam, MemberProfile,SlideShowPhoto,UserPreference,Committee

class MemberProfileAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields':['user']}),
        ('Name', {'fields': ['title','first_name','middle_name','last_name','suffix','nickname','maiden_name']}),
        ('Education/University', {'fields': ['uniqname','UMID','major','standing','expect_grad_date']}),
        ('Chapter', {'fields': ['status','init_chapter','init_term','still_electing']}),
        ('Contact Info', {'fields': ['alt_email','preferred_email','phone','jobs_email']}),
        ('About', {'fields': ['photo','resume','short_bio','gender','shirt_size']}),
        ('Alumni Info', {'fields': ['alum_mail_freq','job_field','employer','meeting_speak'], 'classes':['collapse']}),
    ]
admin.site.register(MemberProfile,MemberProfileAdmin)
admin.site.register(OfficerPosition)
admin.site.register(OfficerTeam)
admin.site.register(Standing)
admin.site.register(Status)
admin.site.register(Major)
admin.site.register(ShirtSize)
admin.site.register(TBPChapter)
admin.site.register(AcademicTerm)
admin.site.register(UserProfile)
admin.site.register(SlideShowPhoto)
admin.site.register(UserPreference)
admin.site.register(Committee)
