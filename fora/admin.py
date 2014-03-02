from django.contrib import admin

from fora.models import Forum,ForumThread,ForumMessage,MessagePoint


# Register your models here.
admin.site.register(Forum)
admin.site.register(ForumThread)
admin.site.register(ForumMessage)
admin.site.register(MessagePoint)

