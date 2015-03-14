import factory

from corporate.models import CorporateTextField, CorporateResourceGuide

CORPORATE_TEXT = r'''A First Level Header
====================

A Second Level Header
---------------------

Now is the time for all good men to come to
the aid of their country. This is just a
regular paragraph.

The quick brown fox jumped over the lazy
dog's back.

### Header 3

> This is a blockquote.
>
> This is the second paragraph in the blockquote.
>
> ## This is an H2 in a blockquote'''

PDF_FILE = 'migweb/test_docs/test.pdf'


class CorporateTextFactory(factory.DjangoModelFactory):
    class Meta:
        model = CorporateTextField
    section = factory.Iterator(['OP', 'CT'])
    text = CORPORATE_TEXT


class CorporateResourceGuideFactory(factory.DjangoModelFactory):
    class Meta:
        model = CorporateResourceGuide
    active = factory.Iterator([True, False])
    name = 'corporate_guide'
    resource_guide = factory.django.FileField(from_path=PDF_FILE)
