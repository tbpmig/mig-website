from django.db import models

# Create your models here.

class Forum(models.Model):
    name = models.CharField(max_length=128)

class ForumThread(models.Model):
    title = models.CharField(max_length=256)
    forum = models.ForeignKey(Forum)
    creator=models.ForeignKey('mig_main.MemberProfile')
    time_created = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)

class ForumMessage(models.Model):
    title = models.CharField(max_length=256)
    content=models.TextField()
    forum_thread = models.ForeignKey(ForumThread)
    previous_version = models.OneToOneField('self',related_name='next_version',null=True,blank=True)
    in_reply_to = models.ForeignKey('self',related_name='replies',null=True,blank=True)
    creator = models.ForeignKey('mig_main.MemberProfile')
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified=models.DateTimeField(auto_now=True)
    score = models.IntegerField(default=0)
    hidden=models.BooleanField(default=False)

class MessagePoint(models.Model):
    message=models.ForeignKey(ForumMessage)
    user = models.ForeignKey('mig_main.MemberProfile')
    plus_point = models.BooleanField()


