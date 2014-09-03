from django.db import models
from django.core.urlresolvers import reverse

from mig_main.models import MemberProfile
from mig_main.templatetags.my_markdown import my_markdown
# Create your models here.
def get_user_points(memberprofile):
    point_objects = MessagePoint.objects.filter(message__creator=memberprofile)
    votes_count = 2*point_objects.filter(plus_point=True,message__hidden=False).count()-point_objects.filter(plus_point=False).count()
    spent_downvotes = MessagePoint.objects.filter(user=memberprofile,plus_point=False).count()
    posts_created = ForumMessage.objects.filter(creator=memberprofile,hidden=False).count()
    return posts_created+votes_count-spent_downvotes
    
class Forum(models.Model):
    name = models.CharField(max_length=128)
    
    def get_first_threads(self):
        threads=self.forumthread_set.filter(hidden=False).order_by('time_created')
        return threads[:9]
class ForumThread(models.Model):
    title = models.CharField(max_length=256)
    forum = models.ForeignKey(Forum)
    creator=models.ForeignKey('mig_main.MemberProfile')
    time_created = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    
    def get_root_message(self):
        messages= self.forummessage_set.filter(in_reply_to=None,hidden=False)
        if messages.exists():
            return messages[0]
        return None
class ForumMessage(models.Model):
    title = models.CharField(max_length=256)
    content=models.TextField()
    forum_thread = models.ForeignKey(ForumThread)
    in_reply_to = models.ForeignKey('self',related_name='replies',null=True,blank=True)
    creator = models.ForeignKey('mig_main.MemberProfile')
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified=models.DateTimeField(auto_now=True)
    score = models.IntegerField(default=0)
    hidden=models.BooleanField(default=False)
    def assemble_replies_helper(self,depth):
        output = [{'reply':self,'depth':depth,'user_points':get_user_points(self.creator),'comment_points':self.get_net_points()}]
        for reply in self.replies.filter(hidden=False).order_by('time_created'):
            output+=reply.assemble_replies_helper(depth+10)
        return output
    def assemble_replies(self):
        if self.hidden:
            return []
        return self.assemble_replies_helper(0)
    
    def get_net_points(self):
        return self.messagepoint_set.filter(plus_point=True).count()-self.messagepoint_set.filter(plus_point=False).count()
    def get_upvoters(self):
        return MemberProfile.objects.filter(messagepoint__in=self.messagepoint_set.filter(plus_point=True))
    def get_downvoters(self):
        return MemberProfile.objects.filter(messagepoint__in=self.messagepoint_set.filter(plus_point=False))
class MessagePoint(models.Model):
    message=models.ForeignKey(ForumMessage)
    user = models.ForeignKey('mig_main.MemberProfile')
    plus_point = models.BooleanField()


