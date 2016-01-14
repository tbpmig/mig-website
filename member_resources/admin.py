from django.contrib import admin
from member_resources.models import (
                ActiveList,
                GradElecteeList,
                UndergradElecteeList,
                ProjectLeaderList,
)

admin.site.register(ActiveList)
admin.site.register(GradElecteeList)
admin.site.register(UndergradElecteeList)
admin.site.register(ProjectLeaderList)
