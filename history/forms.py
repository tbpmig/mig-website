from django.forms import ModelForm
from history.models import Publication, WebsiteArticle

class ArticleForm(ModelForm):
    class Meta:
        model = Publication

class WebArticleForm(ModelForm):
    class Meta:
        model = WebsiteArticle
        exclude = ['created_by']
