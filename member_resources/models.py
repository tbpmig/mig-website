from django.db import models

from django.core.validators import RegexValidator
# Create your models here

class MemberList(models.Model):
    class Meta:
        abstract = True

    uniqname = models.CharField(max_length=8,
                                validators =[RegexValidator(regex=r'^[a-z]{3,8}$',
                                message="Uniqnames must be 3-8 characters, all letters")])
    def __unicode__(self):
        return self.uniqname
                                
class ActiveList(MemberList):
    pass

class GradElecteeList(MemberList):
    pass
    
class UndergradElecteeList(MemberList):
    pass

class ProjectLeaderList(models.Model):
    member_profile = models.ForeignKey('mig_main.MemberProfile')
