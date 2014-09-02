from django.db import models
from django.core.urlresolvers import reverse
from mig_main.templatetags.my_markdown import my_markdown
# Create your models here.
def get_user_points(memberprofile):
    point_objects = MessagePoint.objects.filter(user=memberprofile)
    votes_count = 2*point_objects.filter(plus_point=True).count()-point_objects.filter(plus_point=False).count()
    spent_downvotes = DownVoteSpent.objects.filter(user=memberprofile).count()
    posts_created = ForumMessage.objects.filter(creator=memberprofile).count()
    return posts_created+votes_count-spent_downvotes
    
class Forum(models.Model):
    name = models.CharField(max_length=128)
    
    def get_first_threads(self):
        threads=self.forumthread_set.order_by('time_created')
        return threads[:9]
class ForumThread(models.Model):
    title = models.CharField(max_length=256)
    forum = models.ForeignKey(Forum)
    creator=models.ForeignKey('mig_main.MemberProfile')
    time_created = models.DateTimeField(auto_now_add=True)
    hidden = models.BooleanField(default=False)
    
    def get_root_message(self):
        messages= self.forummessage_set.filter(in_reply_to=None)
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
    
 
    def print_replies(self):
        output_string = ''
        output_string+=r'''
        <div class="forum-post"> 
        <h4>%(title)s</h4>
        <em>By: %(author)s %(time)s</em>
        %(body)s
        <a class="btn btn-default" href="%(link)s">Post Reply</a>
        </div>'''%{'title':self.title,'author':unicode(self.creator),'time':self.time_created.strftime('%d %b %Y %I:%M%p'),'body':my_markdown(self.content),'link':reverse('fora:add_comment',args=(self.forum_thread.forum.id,self.id))}
        for reply in self.replies.all():
            output_string+='<div style=\"padding-left:10px;\">'+reply.print_replies()+'</div>'
        return output_string

class MessagePoint(models.Model):
    message=models.ForeignKey(ForumMessage)
    user = models.ForeignKey('mig_main.MemberProfile')
    plus_point = models.BooleanField()

class DownVoteSpent(models.Model):
    user = models.ForeignKey('mig_main.MemberProfile')

